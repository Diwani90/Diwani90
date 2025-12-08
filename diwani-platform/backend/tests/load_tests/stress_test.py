#!/usr/bin/env python3
"""
اختبار الضغط البسيط - Stress Test
==================================

اختبار ضغط بسيط باستخدام concurrent.futures
لا يحتاج تثبيت مكتبات إضافية

التشغيل:
    python stress_test.py --host http://localhost:8000 --users 50 --duration 60
"""

import argparse
import json
import random
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
import urllib.request
import urllib.error
import urllib.parse
from collections import defaultdict


# =============================================
# نتائج الاختبار
# =============================================

@dataclass
class RequestResult:
    """نتيجة طلب واحد"""
    endpoint: str
    method: str
    status_code: int
    response_time: float  # بالميلي ثانية
    success: bool
    error: str = None


@dataclass
class TestResults:
    """نتائج الاختبار الكلية"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    endpoint_stats: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    start_time: float = 0
    end_time: float = 0

    def add_result(self, result: RequestResult):
        self.total_requests += 1
        if result.success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if result.error:
                self.errors[result.error] += 1

        self.response_times.append(result.response_time)
        self.endpoint_stats[result.endpoint].append(result.response_time)

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0
        return statistics.mean(self.response_times)

    @property
    def p50_response_time(self) -> float:
        if not self.response_times:
            return 0
        return statistics.median(self.response_times)

    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx] if idx < len(sorted_times) else sorted_times[-1]

    @property
    def p99_response_time(self) -> float:
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[idx] if idx < len(sorted_times) else sorted_times[-1]

    @property
    def requests_per_second(self) -> float:
        duration = self.end_time - self.start_time
        if duration == 0:
            return 0
        return self.total_requests / duration


# =============================================
# عميل HTTP بسيط
# =============================================

class SimpleHTTPClient:
    """عميل HTTP بسيط للاختبارات"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def request(self, method: str, path: str, headers: dict = None, data: dict = None) -> RequestResult:
        """إرسال طلب HTTP"""
        url = f"{self.base_url}{path}"
        headers = headers or {}
        headers['Content-Type'] = 'application/json'

        start_time = time.time()

        try:
            req_data = json.dumps(data).encode('utf-8') if data else None
            req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

            with urllib.request.urlopen(req, timeout=30) as response:
                response_time = (time.time() - start_time) * 1000  # تحويل لميلي ثانية
                return RequestResult(
                    endpoint=path,
                    method=method,
                    status_code=response.status,
                    response_time=response_time,
                    success=200 <= response.status < 400
                )

        except urllib.error.HTTPError as e:
            response_time = (time.time() - start_time) * 1000
            return RequestResult(
                endpoint=path,
                method=method,
                status_code=e.code,
                response_time=response_time,
                success=False,
                error=f"HTTP {e.code}"
            )

        except urllib.error.URLError as e:
            response_time = (time.time() - start_time) * 1000
            return RequestResult(
                endpoint=path,
                method=method,
                status_code=0,
                response_time=response_time,
                success=False,
                error=str(e.reason)
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return RequestResult(
                endpoint=path,
                method=method,
                status_code=0,
                response_time=response_time,
                success=False,
                error=str(e)
            )

    def get(self, path: str, headers: dict = None) -> RequestResult:
        return self.request('GET', path, headers)

    def post(self, path: str, data: dict = None, headers: dict = None) -> RequestResult:
        return self.request('POST', path, headers, data)


# =============================================
# سيناريوهات الاختبار
# =============================================

class TestScenarios:
    """سيناريوهات الاختبار"""

    def __init__(self, client: SimpleHTTPClient):
        self.client = client

    def get_random_scenario(self) -> callable:
        """اختيار سيناريو عشوائي"""
        scenarios = [
            (self.platform_stats, 10),      # وزن 10
            (self.browse_products, 8),      # وزن 8
            (self.search_products, 5),      # وزن 5
            (self.browse_stores, 5),        # وزن 5
            (self.health_check, 3),         # وزن 3
        ]

        # اختيار موزون
        total_weight = sum(w for _, w in scenarios)
        r = random.uniform(0, total_weight)
        cumulative = 0
        for scenario, weight in scenarios:
            cumulative += weight
            if r <= cumulative:
                return scenario

        return scenarios[0][0]

    def platform_stats(self) -> RequestResult:
        """إحصائيات المنصة"""
        return self.client.get('/api/v1/platform/stats/')

    def browse_products(self) -> RequestResult:
        """تصفح المنتجات"""
        page = random.randint(1, 5)
        return self.client.get(f'/api/v1/products/products?limit=20&offset={page * 20}')

    def search_products(self) -> RequestResult:
        """البحث عن منتجات"""
        terms = ['أسمنت', 'حديد', 'رمل', 'طوب', 'جبس', 'خرسانة', 'بلاط']
        term = random.choice(terms)
        encoded_term = urllib.parse.quote(term)
        return self.client.get(f'/api/v1/search/products?q={encoded_term}')

    def browse_stores(self) -> RequestResult:
        """تصفح المتاجر"""
        return self.client.get('/api/v1/stores/stores?limit=20')

    def health_check(self) -> RequestResult:
        """فحص الصحة"""
        return self.client.get('/health/')


# =============================================
# محرك الاختبار
# =============================================

class StressTestRunner:
    """محرك تشغيل اختبار الضغط"""

    def __init__(self, host: str, num_users: int, duration: int):
        self.host = host
        self.num_users = num_users
        self.duration = duration  # بالثواني
        self.results = TestResults()
        self.running = True

    def worker(self, user_id: int) -> List[RequestResult]:
        """عامل واحد يمثل مستخدم"""
        client = SimpleHTTPClient(self.host)
        scenarios = TestScenarios(client)
        user_results = []

        while self.running:
            scenario = scenarios.get_random_scenario()
            result = scenario()
            user_results.append(result)

            # انتظار عشوائي بين الطلبات (1-3 ثواني)
            time.sleep(random.uniform(0.5, 2))

        return user_results

    def run(self) -> TestResults:
        """تشغيل الاختبار"""
        print(f"\n{'='*60}")
        print(f"بدء اختبار الضغط")
        print(f"{'='*60}")
        print(f"المضيف: {self.host}")
        print(f"عدد المستخدمين المتزامنين: {self.num_users}")
        print(f"مدة الاختبار: {self.duration} ثانية")
        print(f"{'='*60}\n")

        self.results.start_time = time.time()
        all_results = []

        with ThreadPoolExecutor(max_workers=self.num_users) as executor:
            futures = [executor.submit(self.worker, i) for i in range(self.num_users)]

            # الانتظار للمدة المحددة
            time.sleep(self.duration)
            self.running = False

            # جمع النتائج
            for future in as_completed(futures, timeout=30):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"خطأ في العامل: {e}")

        self.results.end_time = time.time()

        # تجميع النتائج
        for result in all_results:
            self.results.add_result(result)

        return self.results

    def print_report(self):
        """طباعة تقرير النتائج"""
        r = self.results
        duration = r.end_time - r.start_time

        print(f"\n{'='*60}")
        print(f"تقرير اختبار الضغط")
        print(f"{'='*60}")
        print(f"\nمعلومات الاختبار:")
        print(f"  - المدة الفعلية: {duration:.2f} ثانية")
        print(f"  - عدد المستخدمين: {self.num_users}")

        print(f"\nإحصائيات الطلبات:")
        print(f"  - إجمالي الطلبات: {r.total_requests}")
        print(f"  - الطلبات الناجحة: {r.successful_requests}")
        print(f"  - الطلبات الفاشلة: {r.failed_requests}")
        print(f"  - نسبة النجاح: {r.success_rate:.2f}%")
        print(f"  - الطلبات/ثانية: {r.requests_per_second:.2f}")

        print(f"\nأوقات الاستجابة (ميلي ثانية):")
        print(f"  - المتوسط: {r.avg_response_time:.2f} ms")
        print(f"  - P50 (الوسيط): {r.p50_response_time:.2f} ms")
        print(f"  - P95: {r.p95_response_time:.2f} ms")
        print(f"  - P99: {r.p99_response_time:.2f} ms")

        if r.endpoint_stats:
            print(f"\nإحصائيات حسب الـ Endpoint:")
            for endpoint, times in sorted(r.endpoint_stats.items()):
                avg = statistics.mean(times) if times else 0
                count = len(times)
                print(f"  - {endpoint}: {count} طلب، متوسط {avg:.2f} ms")

        if r.errors:
            print(f"\nالأخطاء:")
            for error, count in sorted(r.errors.items(), key=lambda x: -x[1]):
                print(f"  - {error}: {count} مرة")

        # تقييم الأداء
        print(f"\n{'='*60}")
        print(f"تقييم الأداء")
        print(f"{'='*60}")

        issues = []
        if r.success_rate < 99:
            issues.append(f"⚠️ نسبة النجاح منخفضة ({r.success_rate:.2f}%)")
        if r.avg_response_time > 500:
            issues.append(f"⚠️ متوسط وقت الاستجابة مرتفع ({r.avg_response_time:.2f} ms)")
        if r.p95_response_time > 1000:
            issues.append(f"⚠️ P95 مرتفع ({r.p95_response_time:.2f} ms)")
        if r.requests_per_second < 10:
            issues.append(f"⚠️ معدل الطلبات منخفض ({r.requests_per_second:.2f}/ثانية)")

        if issues:
            print("المشاكل المكتشفة:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("✅ الأداء جيد! لا توجد مشاكل واضحة.")

        print(f"\n{'='*60}\n")


# =============================================
# نقطة الدخول
# =============================================

def main():
    parser = argparse.ArgumentParser(description='اختبار ضغط منصة ديواني')
    parser.add_argument('--host', default='http://localhost:8000', help='عنوان الخادم')
    parser.add_argument('--users', type=int, default=10, help='عدد المستخدمين المتزامنين')
    parser.add_argument('--duration', type=int, default=30, help='مدة الاختبار بالثواني')

    args = parser.parse_args()

    runner = StressTestRunner(args.host, args.users, args.duration)

    try:
        runner.run()
        runner.print_report()
    except KeyboardInterrupt:
        print("\nتم إيقاف الاختبار")
        runner.running = False
        runner.print_report()


if __name__ == '__main__':
    main()
