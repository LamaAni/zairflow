# Examples for using kubernetes yaml

## A single pod implementation using a git autosync to load the dags/plugins into airflow

#### File: `single_pod.yaml`
#### Commands:
```shell
kubectl -f ./single_pod.yaml apply
kubectl port-forward zairflow-tester 8080:8080 # airflow at localhost:3030
kubectl -f ./single_pod.yaml delete
```
## A multi deployment implementation using a git autosync to load the dags/plugins into airflow

#### File: `single_pod.yaml`
#### Commands:
```shell
kubectl -f ./multi_deployment.yaml apply
kubectl port-forward svc/zairflow-test-webserver-svc 8080:8080 # airflow at localhost:3030
kubectl -f ./multi_deployment.yaml delete
```
