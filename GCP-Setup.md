# Setting up Valkey and a VM on GCP for Semantic Search

## Clone this Terraform repo

```bash
git clone https://github.com/maguec/ValkeyPerfTest
cd ValkeyPerfTest
```

## Create a variable file

create standalone_valkey.tfvars

```
gcp_project_id = "<GCP_PROJECT>"
gcp_zone       = "us-west1-a"
valkey_version = "VALKEY_9_0"
enable_redis   = false
valkey_mode    = "CLUSTER_DISABLED"
cluster_nodes  = 1
```

## Apply the Terraform

```bash
terraform apply -var-file=standalone_valkey.tfvars
```

## SSH into the instance

After applying the terraform you should see command like

```
gcloud compute ssh --zone <ZONE_ABOVE> vm-<RANDOM_STRING> --project <GCP_PROJECT>
```

Use this to SSH in

## Setup the application

```bash
git clone https://github.com/maguec/ValkeySemanticCache
cd ValkeySemanticCache
cp .env-example .env
# Get the IP of your Valkey instance
echo $GOOGLE_VALKEY_IP
```

Edit the file - you won't need a password for Valkey so your URL should look like

```bash
redis://<IP_ABOVE>:6379/0
```

To get the url for the web UI get the IP address from the vm

```bash
curl -4 ifconfig.co
```

Then your URL will be http://<IP_ADDRESS>:8080 instead of localhost


## Destroy your environment

When your testing is complete

```bash
terraform destroy -var-file=standalone_valkey.tfvars
```
