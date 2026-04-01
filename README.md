Warning: for deployment, place this workload in a VNet instead of exposing it directly on the public internet.

# Ollama in Azure

This repository documents a CPU-only Ollama deployment on Azure Container Instances (ACI) for embedding workloads.

The current working path in this repo uses `mxbai-embed-large` and is designed for a simple container-based Azure deployment.

## What This Repo Contains

- `Dockerfile`: builds a self-hosted Ollama image for Azure
- `entrypoint.sh`: starts the containerized service
- `self-hosted-ollama.py` and `olama.py`: Python-side app logic used in the Ollama container

## Architecture

### Ollama on Azure Container Instances

This path is designed for a lightweight CPU-only deployment:

- Container image built in Azure Container Registry (ACR)
- Private ACR pull secured with a user-assigned managed identity
- Azure Container Instances exposes port `11434`
- Default Ollama model is `mxbai-embed-large`

This is the simplest path in the repo and the one that has already been validated end to end.

## Prerequisites

- Azure CLI installed and authenticated with `az login`
- Access to an Azure subscription and resource group
- Permission to create ACR, managed identity, and container resources
- Docker access is only required if you build locally; the ACI path in this repo uses `az acr build`

## Values To Replace Before Azure Deployment

The deployment commands in this README use placeholders. Replace these with values from your own Azure environment before running them.

- `<acr-name>`: the name of your Azure Container Registry, for example `myollamaregistry`
- `<resource-group>`: an existing resource group that will contain the managed identity and Azure Container Instance, for example `rg-ollama-demo`
- `<managed-identity-name>`: the name of the user-assigned managed identity used for ACR pulls, for example `mi-aci-ollama-pull`
- `<location>`: the Azure region for the identity and container deployment, for example `eastus2`
- `<container-name>`: the Azure Container Instance container group name, for example `aci-self-hosted-ollama`
- `<public-ip>`: the public IP address assigned to the deployed Azure Container Instance, used only when validating the endpoint after deployment
- `OLLAMA_BASE_URL`: the base URL used by `olama.py`, for example `http://<public-ip>:11434/v1`
- `[caller]`: the Azure CLI caller identity used by `az acr build` when the registry uses ABAC repository permissions; keep this literal value only if your ACR requires it

You do not need to replace `self-hosted-ollama`, `v1`, or `v1-amd64` unless you intentionally want a different repository name or image tag.

Example values:

```text
<acr-name> = myollamaregistry
<resource-group> = rg-ollama-demo
<managed-identity-name> = mi-aci-ollama-pull
<location> = eastus2
<container-name> = aci-self-hosted-ollama
<public-ip> = <assigned-after-deploy>
OLLAMA_BASE_URL = http://<public-ip>:11434/v1
[caller] = [caller]
```

With those example values, the container deployment command would look like this:

```powershell
$identityId = az identity show -g rg-ollama-demo -n mi-aci-ollama-pull --query id -o tsv

az container create \
  -g rg-ollama-demo \
  -n aci-self-hosted-ollama \
  --image myollamaregistry.azurecr.io/self-hosted-ollama:v1-amd64 \
  --assign-identity $identityId \
  --acr-identity $identityId \
  --cpu 2 \
  --memory 8 \
  --ports 11434 \
  --ip-address Public \
  --os-type Linux \
  --restart-policy Always \
  -o json
```

## Deploy Ollama to Azure Container Instances

### 1. Build and push the image to ACR

Use Azure Container Registry build instead of a local Docker build:

```powershell
az acr build --registry <acr-name> --image self-hosted-ollama:v1 --source-acr-auth-id [caller] .
```

If you are deploying to ACI, build an `amd64` image explicitly:

```powershell
az acr build --registry <acr-name> --image self-hosted-ollama:v1-amd64 --platform linux/amd64 --source-acr-auth-id [caller] .
```

Verify the pushed tags:

```powershell
az acr repository show-tags --name <acr-name> --repository self-hosted-ollama --output table
```

### 2. Register the ACI resource provider if needed

```powershell
az provider register --namespace Microsoft.ContainerInstance
az provider register --namespace Microsoft.ContainerInstance --wait
az provider show --namespace Microsoft.ContainerInstance --query "{namespace:namespace,registrationState:registrationState}" -o json
```

### 3. Create a managed identity for ACR pulls

```powershell
az identity create -g <resource-group> -n <managed-identity-name> --location <location> --query "{id:id,principalId:principalId,name:name}" -o json
```

Grant the identity pull access to the registry:

```powershell
az role assignment create --assignee-object-id $(az identity show -g <resource-group> -n <managed-identity-name> --query principalId -o tsv) --assignee-principal-type ServicePrincipal --scope $(az acr show -n <acr-name> --query id -o tsv) --role "Container Registry Repository Reader" -o json
```

### 4. Deploy the container to ACI

```powershell
$identityId = az identity show -g <resource-group> -n <managed-identity-name> --query id -o tsv

az container create \
  -g <resource-group> \
  -n <container-name> \
  --image <acr-name>.azurecr.io/self-hosted-ollama:v1-amd64 \
  --assign-identity $identityId \
  --acr-identity $identityId \
  --cpu 2 \
  --memory 8 \
  --ports 11434 \
  --ip-address Public \
  --os-type Linux \
  --restart-policy Always \
  -o json
```

### 5. Validate the deployment

Check status:

```powershell
az container show -g <resource-group> -n <container-name> --query "{name:name,provisioningState:provisioningState,state:containers[0].instanceView.currentState.state,ipAddress:ipAddress.ip,ports:ipAddress.ports}" -o json
```

View logs:

```powershell
az container logs -g <resource-group> -n <container-name>
```

Test the public endpoint:

```powershell
Invoke-WebRequest -UseBasicParsing http://<public-ip>:11434/api/tags | Select-Object -ExpandProperty Content
```

## ACI Operational Notes

- ACI required a `linux/amd64` image in validation, so `v1-amd64` was used for deployment.
- The example ACR used `AbacRepositoryPermissions`, so `--source-acr-auth-id [caller]` was required for `az acr build`.
- The ACI endpoint is public and unauthenticated unless you add a private ingress or proxy in front of it.
- The model is stored inside the container filesystem, so a redeploy can require the model to be pulled again unless you add persistent storage.

## Cost Snapshot For The ACI Shape

The validated ACI deployment shape was:

- Region: `eastus2`
- CPU: `2 vCPU`
- Memory: `8 GB`
- Restart policy: `Always`

Using the pricing inputs captured during validation, the compute-only estimate was:

- About `$102.08` per month
- About `$3.40` per day

This estimate does not include ACR storage, network egress, or Azure Files if persistence is added.

## Capacity Snapshot For The ACI Shape

The following numbers were measured against a live embeddings endpoint using `mxbai-embed-large` on a CPU-only ACI deployment.

Sequential benchmark snapshot:

- 10 requests in `3.513s`
- Average latency: about `0.351s`
- Throughput: about `2.85 req/s`

Longer sequential benchmark snapshot:

- 30 requests in `7.810s`
- Average latency: about `0.260s`
- Throughput: about `3.84 req/s`

Working planning estimate:

- Safe planning number: about `3 req/s`
- Warmed-up estimate: about `4 req/s`
- Equivalent: about `180` to `240` embedding requests per minute

Concurrency snapshot:

- Throughput improved through roughly `6` concurrent active requests
- Aggregate throughput started degrading at about `8` concurrent requests
- Practical safe range: about `4` to `6` active concurrent users

These figures are for embeddings with small test inputs. They should not be treated as chat-generation capacity numbers.

## Security Considerations

- The ACI example exposes a public unauthenticated endpoint on port `11434`
- If you intend to publish or productionize this, place the service behind authentication, private networking, or an API gateway

## Suggested Next Improvements

- Add persistent model storage for the ACI path
- Put the public endpoint behind APIM, Front Door, or another authenticated gateway
- Add repeatable benchmark scripts to the repo instead of keeping results only in notes
