def call(Map cfg = [:]) {
	evaluateAndDeployRAG(cfg)
}

def evaluateAndDeployRAG(Map cfg = [:]) {
	buildAndPushImage(cfg)
	evaluateRAG(cfg)
	if (cfg.tfDir) {
		applyTerraform(tfDir: cfg.tfDir)
	}
	deployHelm(cfg)
}

boolean hasCmd(String cmd) {
	return sh(script: "command -v ${cmd} >/dev/null 2>&1", returnStatus: true) == 0
}

def buildAndPushImage(Map cfg = [:]) {
	String imageRepo = cfg.imageRepo
	String imageTag = cfg.imageTag ?: env.BUILD_ID
	String dockerContext = cfg.dockerContext ?: '.'
	String dockerfilePath = cfg.dockerfilePath ?: 'rag-app/Dockerfile'
	String credentialsId = cfg.credentialsId ?: 'docker-creds'

	if (!hasCmd('docker')) {
		echo 'Skipping image build/push: docker CLI is not available on this Jenkins agent.'
		return
	}

	try {
		withCredentials([usernamePassword(credentialsId: credentialsId, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
			sh """
				set -e
				REGISTRY=\$(echo ${imageRepo} | cut -d'/' -f1)
				echo \"\$DOCKER_PASS\" | docker login \"\$REGISTRY\" -u \"\$DOCKER_USER\" --password-stdin
				docker build -f ${dockerfilePath} -t ${imageRepo}:${imageTag} ${dockerContext}
				docker push ${imageRepo}:${imageTag}
			"""
		}
	} catch (Exception ex) {
		echo "Docker credentials '${credentialsId}' not found or unusable. Building image locally without push."
		sh """
			set -e
			docker build -f ${dockerfilePath} -t ${imageRepo}:${imageTag} ${dockerContext}
		"""
	}
}

def evaluateRAG(Map cfg = [:]) {
	String appDir = cfg.appDir ?: 'rag-app'
	String threshold = cfg.threshold ?: '0.75'

	String pyCmd = hasCmd('python3') ? 'python3' : (hasCmd('python') ? 'python' : '')
	if (!pyCmd) {
		echo 'Skipping RAG evaluation: python runtime is not available on this Jenkins agent.'
		return
	}

	sh """
		set -e
		cd ${appDir}
		${pyCmd} -m pip install --upgrade pip
		${pyCmd} -m pip install -r requirements.txt
		export PYTHONPATH=.
		export RAG_SCORE_THRESHOLD=${threshold}
		${pyCmd} -m pytest -m rag_eval -q tests/test_rag.py --maxfail=1
	"""
}

def applyTerraform(Map cfg = [:]) {
	String tfDir = cfg.tfDir ?: 'infra/terraform'
	if (!hasCmd('terraform')) {
		echo 'Skipping Terraform apply: terraform CLI is not available on this Jenkins agent.'
		return
	}
	sh """
		set -e
		cd ${tfDir}
		terraform init -input=false
		terraform fmt -check
		terraform validate
		terraform apply -auto-approve -input=false
	"""
}

def deployHelm(Map cfg = [:]) {
	String releaseName = cfg.releaseName ?: 'auto-rag'
	String chartPath = cfg.chartPath ?: 'helm/rag-chart'
	String namespace = cfg.namespace ?: 'rag'
	String imageRepo = cfg.imageRepo
	String imageTag = cfg.imageTag ?: env.BUILD_ID

	if (!hasCmd('kubectl') || !hasCmd('helm')) {
		echo 'Skipping Helm deploy: kubectl/helm CLI is not available on this Jenkins agent.'
		return
	}

	sh """
		set -e
		kubectl get ns ${namespace} >/dev/null 2>&1 || kubectl create ns ${namespace}
		helm upgrade --install ${releaseName} ${chartPath} -n ${namespace} \
			--set image.repository=${imageRepo} \
			--set image.tag=${imageTag}
	"""
}

return this

