variable "kubeconfig_path" {
	type        = string
	description = "Absolute path to kubeconfig"
	default     = "~/.kube/config"
}

variable "namespace" {
	type        = string
	description = "Kubernetes namespace for Auto-RAG"
	default     = "rag"
}

variable "environment" {
	type        = string
	description = "Environment name"
	default     = "dev"
}

variable "pvc_size" {
	type        = string
	description = "PVC size for vector DB"
	default     = "10Gi"
}

variable "storage_class" {
	type        = string
	description = "StorageClass used by PVC"
	default     = "standard"
}

