def get_server_status(server_name):
  server = {
    "web-01": {
      "status": "healthy",
      "cpu": 42
    },
    "web-02": {
      "status": "unhealthy",
      "cpu": 95
    },
    "web-03": {
      "status": "healthy",
      "cpu": 15
    }
  }
  return server.get(
    server_name,
    {
       "status": "unknown"
    }
  )

result = get_server_status("web-02")
print(result)
print(get_server_status("web-01"))
print(get_server_status(""))