output "namespace" {
	description = "RAG namespace"
	value       = kubernetes_namespace.rag.metadata[0].name
}

output "vectordb_pvc" {
	description = "PVC name for vector DB"
	value       = kubernetes_persistent_volume_claim.vectordb.metadata[0].name
}

