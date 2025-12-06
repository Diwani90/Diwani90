# Docker Secrets

This directory contains secret files for Docker Swarm/Compose secrets.

## Required Files

Create these files with your production secrets:

```bash
# Django secret key (generate a strong random key)
echo "your-strong-random-secret-key" > django_secret.txt

# Database password
echo "your-strong-db-password" > db_password.txt
```

## Security Notes

- **NEVER** commit actual secrets to version control
- Use strong, randomly generated passwords
- Rotate secrets regularly
- Restrict file permissions: `chmod 600 *.txt`
