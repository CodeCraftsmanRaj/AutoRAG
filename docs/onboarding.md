# Onboarding

## Local quickstart (minikube-first)

1. Start cluster: `minikube start`
2. Install prerequisites: Docker, Helm, kubectl, Terraform, Jenkins
3. Build app image and push to your registry
4. Set Helm secret value (`OPENAI_API_KEY`)
5. Deploy with `helm upgrade --install auto-rag helm/rag-chart -n rag --create-namespace`

## Core flow

- Commit docs/prompts/code
- Jenkins runs Sonar + RAG evaluation
- Only successful RAG metrics pass deployment gates

