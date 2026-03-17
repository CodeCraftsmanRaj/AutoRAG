# Jenkins Shared Library for Auto-RAG

Expose this library in Jenkins as `rag-shared-lib` and call `ragPipeline(...)` or explicit methods:

- `ragPipeline.buildAndPushImage(...)`
- `ragPipeline.evaluateRAG(...)`
- `ragPipeline.applyTerraform(...)`
- `ragPipeline.deployHelm(...)`
- `ragPipeline.evaluateAndDeployRAG(...)`

Example in Jenkinsfile:

```
@Library('rag-shared-lib@main') _

pipeline {
	agent any
	stages {
		stage('RAG CD') {
			steps {
				script {
					ragPipeline.evaluateAndDeployRAG(
						imageRepo: 'ghcr.io/acme/rag',
						imageTag: env.BUILD_ID,
						appDir: 'rag-app',
						threshold: '0.75',
						tfDir: 'infra/terraform',
						releaseName: 'auto-rag',
						chartPath: 'helm/rag-chart',
						namespace: 'rag'
					)
				}
			}
		}
	}
}
```

