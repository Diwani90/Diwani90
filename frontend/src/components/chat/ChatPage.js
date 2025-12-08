import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  UserCircleIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

const ChatPage = () => {
  const { conversationId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();

  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  // معالجة معامل with لبدء محادثة جديدة
  const withUserId = searchParams.get('with');

  useEffect(() => {
    fetchConversations();
  }, []);

  // بدء محادثة جديدة إذا وجد معامل with
  useEffect(() => {
    if (withUserId && !loading) {
      startNewConversation(parseInt(withUserId));
    }
  }, [withUserId, loading]);

  useEffect(() => {
    if (conversationId) {
      const conversation = conversations.find(c => c.conversation_id === conversationId);
      if (conversation) {
        setSelectedConversation(conversation);
        fetchMessages(conversationId);
      }
    }
  }, [conversationId, conversations]);

  const startNewConversation = async (userId) => {
    try {
      const response = await axios.post('/chat/start', null, {
        params: { user_id: userId }
      });

      if (response.data.success) {
        // إضافة المحادثة للقائمة إذا لم تكن موجودة
        const existingConv = conversations.find(c => c.conversation_id === response.data.conversation_id);
        if (!existingConv) {
          const newConv = {
            conversation_id: response.data.conversation_id,
            other_user: response.data.other_user,
            unread_count: response.data.unread_count,
            last_message: null,
          };
          setConversations(prev => [newConv, ...prev]);
          setSelectedConversation(newConv);
        } else {
          setSelectedConversation(existingConv);
        }

        // إزالة معامل with من الـ URL
        navigate('/chat', { replace: true });
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
      toast.error('خطأ', 'حدث خطأ في بدء المحادثة');
    }
  };

  const fetchConversations = async () => {
    try {
      const response = await axios.get('/chat/conversations');
      setConversations(response.data.conversations || []);
    } catch (error) {
      console.error('Error fetching conversations:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل المحادثات');
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (convId) => {
    try {
      const response = await axios.get(`/chat/${convId}/messages`);
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Error fetching messages:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل الرسائل');
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim() || !selectedConversation) {
      return;
    }

    setSending(true);
    
    try {
      const messageData = {
        receiver_id: selectedConversation.other_user.id,
        content: newMessage.trim(),
        message_type: 'text'
      };
      
      const response = await axios.post('/chat/send', messageData);
      
      setMessages(prev => [...prev, response.data]);
      setNewMessage('');
      
      // Update conversation list
      setConversations(prev => 
        prev.map(conv => 
          conv.conversation_id === selectedConversation.conversation_id
            ? { ...conv, last_message: response.data }
            : conv
        )
      );
      
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('خطأ', 'حدث خطأ في إرسال الرسالة');
    } finally {
      setSending(false);
    }
  };

  const selectConversation = (conversation) => {
    setSelectedConversation(conversation);
    fetchMessages(conversation.conversation_id);
    
    // Mark as read
    setConversations(prev =>
      prev.map(conv =>
        conv.conversation_id === conversation.conversation_id
          ? { ...conv, unread_count: 0 }
          : conv
      )
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-4 h-screen">
          {/* Conversations Sidebar */}
          <div className="lg:col-span-1 bg-white border-l border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <h1 className="text-xl font-bold text-gray-900 flex items-center">
                <ChatBubbleLeftRightIcon className="h-6 w-6 ml-2" />
                المحادثات
              </h1>
            </div>
            
            {/* Search */}
            <div className="p-4 border-b border-gray-200">
              <div className="relative">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 absolute right-3 top-1/2 transform -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="البحث في المحادثات..."
                  className="input-field pr-10 text-sm"
                />
              </div>
            </div>

            {/* Conversations List */}
            <div className="overflow-y-auto" style={{ height: 'calc(100vh - 140px)' }}>
              {conversations.length > 0 ? (
                <div className="space-y-1 p-2">
                  {conversations.map((conversation) => (
                    <button
                      key={conversation.conversation_id}
                      onClick={() => selectConversation(conversation)}
                      className={`w-full text-right p-3 rounded-lg transition-colors duration-200 ${
                        selectedConversation?.conversation_id === conversation.conversation_id
                          ? 'bg-blue-50 border border-blue-200'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center">
                        <div className="bg-gray-300 w-10 h-10 rounded-full flex items-center justify-center ml-3">
                          <UserCircleIcon className="h-6 w-6 text-gray-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-center mb-1">
                            <h3 className="font-medium text-gray-900 truncate">
                              {conversation.other_user?.full_name || 'مستخدم'}
                            </h3>
                            {conversation.unread_count > 0 && (
                              <span className="bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                                {conversation.unread_count}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 truncate">
                            {conversation.other_user?.role === 'supplier' ? conversation.other_user?.company_name : 'عميل'}
                          </p>
                          {conversation.last_message && (
                            <p className="text-xs text-gray-500 truncate mt-1">
                              {conversation.last_message.content}
                            </p>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <ChatBubbleLeftRightIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">لا توجد محادثات</p>
                  <p className="text-sm text-gray-400 mt-1">ابدأ محادثة جديدة من صفحة المنتجات</p>
                </div>
              )}
            </div>
          </div>

          {/* Chat Area */}
          <div className="lg:col-span-3 flex flex-col bg-white">
            {selectedConversation ? (
              <>
                {/* Chat Header */}
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-center">
                    <div className="bg-gray-300 w-10 h-10 rounded-full flex items-center justify-center ml-3">
                      <UserCircleIcon className="h-6 w-6 text-gray-600" />
                    </div>
                    <div>
                      <h2 className="font-semibold text-gray-900">
                        {selectedConversation.other_user?.full_name || 'مستخدم'}
                      </h2>
                      <p className="text-sm text-gray-600">
                        {selectedConversation.other_user?.role === 'supplier' 
                          ? selectedConversation.other_user?.company_name 
                          : 'عميل'
                        }
                      </p>
                    </div>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ height: 'calc(100vh - 180px)' }}>
                  {messages.length > 0 ? (
                    messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.sender_id === user.id ? 'justify-start' : 'justify-end'}`}
                      >
                        <div
                          className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                            message.sender_id === user.id
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-200 text-gray-900'
                          }`}
                        >
                          <p className="text-sm">{message.content}</p>
                          <p className={`text-xs mt-1 ${
                            message.sender_id === user.id ? 'text-blue-100' : 'text-gray-500'
                          }`}>
                            {new Date(message.created_at).toLocaleTimeString('ar-SA', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-12">
                      <ChatBubbleLeftRightIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">لا توجد رسائل</p>
                      <p className="text-sm text-gray-400 mt-1">ابدأ المحادثة بإرسال رسالة</p>
                    </div>
                  )}
                </div>

                {/* Message Input */}
                <div className="p-4 border-t border-gray-200">
                  <form onSubmit={sendMessage} className="flex space-x-4 space-x-reverse">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="اكتب رسالتك..."
                      className="flex-1 input-field"
                      disabled={sending}
                    />
                    <button
                      type="submit"
                      disabled={!newMessage.trim() || sending}
                      className="btn-primary flex items-center justify-center w-12 h-12 rounded-xl"
                    >
                      {sending ? (
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      ) : (
                        <PaperAirplaneIcon className="h-5 w-5" />
                      )}
                    </button>
                  </form>
                </div>
              </>
            ) : (
              /* No Conversation Selected */
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <ChatBubbleLeftRightIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">اختر محادثة</h2>
                  <p className="text-gray-600">اختر محادثة من القائمة لبدء التواصل</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;