k8s_yaml(helm(
  './helm/visualization-api/',
  name='visualization-api',
  values=[
    './helm-values.yaml',
    ],
  ))

k8s_resource(
  'visualization-api',
  labels=['NaaVRE-visualization-api'],
  links=[
    'https://naavre-dev.minikube.test/visualization-api/docs',
    ]
  )

custom_build(
  'ghcr.io/naavre/naavre-visualization-api',
  'docker buildx build . -f Dockerfile -t $EXPECTED_REF',
  [
    './visualization-api/Dockerfile',
    ],
  skips_local_docker=True,
  disable_push=True,
  )
