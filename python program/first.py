# how to use vitual env
# python3 -m venv .venv ==> it will create .venv directory 
# source .venv/bin/activate ==> it is used to acitvate env
# deactivate ==> to deactiviate


print("Hello" "how")
a=10
b="hello"
c=1.5
d=True
e=[1,2,3]
f=(1,2,3)
g={"name": "Abhimanyu"}
h=None
print(type(a))
print(type(b))
print(type(c))
print(type(d))
print(type(e))
print(type(f))
print(type(g))
print(type(h))

f_name = "Abhimanyu"
l_name = "Kumar"
age = 30
salary = 100000.50
is_devops_engineer = True
full_name=f_name + " " + l_name
print(f_name)
print(age)
print(salary)
print(is_devops_engineer)
print(full_name)

#uses of f-string
env="nonprod"
region="eu-west-1"
message= f"Application is deploying in {env} in region {region}"

print(message)

if env == "prod":
  print(f"env is prod")
else:
  print(f"env is nonprod")

name = "Abhimanyu"
role = "Devops Engineer"
aws_region = "eu-west-1"
experience = 10
terraform = False

if terraform:
  print(name)
  print(role)
  print(aws_region)
  print(f"{experience} yrs experience in terraform")
  print(type(name))
  print(type(role))
  print(type(aws_region))
  print(type(experience))
else:
  print(name)
  print(role)
  print(aws_region)
  print(f"No experience in terraform")

n=21
if n % 2 == 0:
  print(f"{n} is even")
else:
  print(f"{n} is odd")

environment = "Production"
approved = False
if environment == "Production" and approved:
  print("production deployemnt is approved and allowed")
else:
  print("Prod deployment not allowed")

# type conversion
replicas="3"
print(type(replicas))
print(type(int(replicas)))

a=bool(1) # output true
b=bool(0) # output false
c=bool("True") # output true
d=bool("False") # output true
e=bool("") # # output false 
f=bool("Anything") # output true if its empty it will false otherwise true
print(f"{a} {b} {c} {d} {e} {f}")

environment = "production"
current_replicas = 3
max_replicas = 5
deployment_approved = True

if environment == "production" and deployment_approved and current_replicas < max_replicas:
    current_replicas = current_replicas + 1
    print(f"Scaling to {current_replicas} replicas")
else:
    print("Scaling not allowed")

#wrtite python program if both CPU and memory are below their maximum values. then server is healthy otherwise unhealthy
cpu_usage = 75
memory_usage = 60
max_cpu = 80
max_memory = 70

if cpu_usage < max_cpu and memory_usage < max_memory:
  print(f"server is healthy")
else:
  print("server is unhealthy")

# Python program to Increase current_instances by 1 only if it is less than max_instances
current_instances = 3
max_instances = 5

if current_instances < max_instances:
  current_instances = current_instances +1
  print("instance is scaled by 1")
else:
  print("No scaling happend")

# write same program if these value came from git action determine whether you can scale up
replicas = "3"
max_replicas = "5"

if int(replicas) < int(max_replicas):
  print("scaling is possible")
else:
  print("scalling cannot be done")

# determine if deployment is allowed or not 
environment = "production"
terraform_enabled = True
approved = False

if environment == "production" and terraform_enabled and approved:
  print("Deployment allowed")
else:
  print("Deployment Not allowed")

#1
environment = "  PRODUCTION  "
print(environment.strip().lower())

#2
regions = "eu-west-1,eu-central-1,ap-south-1"
regions = regions.split(",")
print(regions)

#3
log = "2026-08-29 ERROR: Database connection failed"
if "ERROR" in log:
  print("Error detected")
else:
  print("No error")

#4
instance_id = "i-123456789"
if instance_id.startswith("i-"):
  print("it seems its a instance id")
else:
  print("Not an instance id")

#5
deployment = "  PAYMENT-SERVICE: DEPLOYMENT FAILED  "
deployment=deployment.strip().lower()
if "failed" in deployment:
  print("Deployment failure detected")
else:
  print("deployment succeeded")

#6
services = "payment,order,user,notification"
services = services.split(",")
print("|".join(services))

#list
#1
servers = ["web-01", "web-02", "web-03"]
print(f"first server is {servers[0]}")
print(f"last server is {servers[2]}")
print(f"number of server is {len(servers)}")

#2
servers = ["web-01", "web-02", "web-03"]
servers[1]="web-02-new"
print(servers)

#3
servers = ["web-01", "web-02"]
newlist=["web-03", "web-04"]
servers.extend(newlist)
print(servers)
servers.remove("web-02")
print(servers)

#4
regions = ["eu-west-1", "eu-central-1", "ap-south-1"]
if "ap-south-1" in regions:
  print("Region supported")

#5
servers = ["web-03", "web-01", "web-04", "web-02"]
servers.sort()
print(servers)

#6
servers = ["web-01", "web-02"]
new_servers = ["web-03", "web-04"]

servers.append(new_servers)
print("it will add list as single item to server list", servers)
servers.extend(new_servers)
print(servers)
servers.pop(2)
print(servers)

#7
running_servers = ["web-01", "web-02", "web-03"]
target="web-02"
if target in running_servers:
  print("Deployment target found")
else:
  print("Deployment target not found")

#8
servers = ["web-03", "web-01", "web-04", "web-02"]
length=len(servers)
servers.sort()
print(servers)
servers.append("web-05")
target="web-05"
if target in servers:
  print("target found")
print(f"Final list are {servers}")

# Practice Exercises — Lesson 5 Loop

#1
servers = ["web-01", "web-02", "web-03"]
for i in servers:
  print(f"checking in {i}")

#2
servers = ["web-01", "web-02", "web-03"]
maintenance = ["web-02"]
for i in servers:
  #print(i)
  if i in maintenance:
    print(f"{i} is under maintenance")
  else:
    print(f"{i} is healthy")

#3
for i in range(1,6):
  print(f"Deploy attempting {i}")

#4

attempt=1
while attempt <=3:
  print(f"Attempt {attempt}")
  attempt+=1

#5
servers = ["web-01", "web-02", "web-03", "web-04"]
for i in servers:
  if i == "web-03":
    print(i)
    print("Critical server found")
    break

#6
servers = ["web-01", "web-02", "web-03", "web-04"]
maintenance = ["web-02", "web-04"]

for server in servers:
  if server in maintenance:
    continue
  print(server)

#7
regions = ["eu-west-1", "eu-central-1"]
services = ["payment", "order"]

for region in regions:
  for service in services:
    print(f"{service} is in {region}")

#8
servers = ["web-01", "web-02", "web-03", "web-04"]
server_status = ["running", "stopped", "running", "stopped"]
for index,value in enumerate(servers):
  print(f"{value} is {server_status[index]}")