terraform {
	required_version = ">= 1.6.0"
	required_providers {
		kubernetes = {
			source  = "hashicorp/kubernetes"
			version = ">= 2.26.0"
		}
	}
}

provider "kubernetes" {
	config_path = var.kubeconfig_path
}

resource "kubernetes_namespace" "rag" {
	metadata {
		name = var.namespace
		labels = {
			app = "auto-rag"
			env = var.environment
		}
	}
}

resource "kubernetes_persistent_volume_claim" "vectordb" {
	metadata {
		name      = "rag-vectordb-pvc"
		namespace = kubernetes_namespace.rag.metadata[0].name
	}

	spec {
		access_modes       = ["ReadWriteOnce"]
		storage_class_name = var.storage_class

		resources {
			requests = {
				storage = var.pvc_size
			}
		}
	}
}

