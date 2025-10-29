# DynamoDB Lab for the Rayan Slim Youtube Channel

## Docker Commands Used

```
docker run -it --rm -v $(pwd):/app python:3.9 bash
cd /app
pip install -r requirements.txt
python dynamo_app.py
```

New to Docker? Learn from the highest-rated Docker course online: [https://rayanslim.com/course/docker-course](https://rayanslim.com/course/docker-course)

## Resources Used

```
{
  "userId": "user123",
  "timestamp": "1698768000",
  "email": "user123@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "preferences": {
    "theme": "dark",
    "notifications": true
  },
  "loginCount": 42
}
```

```
  {
    "userId": "user123",
    "timestamp": "1698854400",
    "email": "user123@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "preferences": {
      "theme": "light",
      "notifications": false
    },
    "loginCount": 45
  }
```
```
    {
    "userId": "user456",
    "timestamp": "1698940800",
    "email": "user456@example.com",
    "firstName": "Jane",
    "lastName": "Smith",
    "status": "premium",
    "loginCount": 128
  }
```
