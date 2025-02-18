import os
import time
import uuid
import grpc
from cri_api.v1 import api_pb2, api_pb2_grpc

# Crear un canal gRPC e inicializar stubs
channel = grpc.insecure_channel("unix:/var/run/crio/crio.sock")
runtime_stub = api_pb2_grpc.RuntimeServiceStub(channel)
image_stub = api_pb2_grpc.ImageServiceStub(channel)

# Función para listar contenedores en ejecución
def list_containers():
    containers = runtime_stub.ListContainers(api_pb2.ListContainersRequest()).containers
    if not containers:
        print("No hay contenedores en ejecución.")
        return []
    for c in containers:
        print(f"ID: {c.id}, Imagen: {c.image.image}, Estado: {c.state}")
    return containers

# Función para crear un contenedor
def create_container(image_name="imagenzenoh2"):
    print(f"Verificando imágenes disponibles para {image_name}...")
    image_list = image_stub.ListImages(api_pb2.ListImagesRequest()).images
    image_id = next((i.id for i in image_list if any(image_name in r for r in i.repo_tags)), None)

    if not image_id:
        print(f"Imagen {image_name} no encontrada. Descargando...")
        image_stub.PullImage(api_pb2.PullImageRequest(image=api_pb2.ImageSpec(image=image_name)))
        print("Imagen descargada.")

    # Crear PodSandbox con UID
    pod_uid = str(uuid.uuid4())
    sandbox_metadata = api_pb2.PodSandboxMetadata(name="sandbox", uid=pod_uid, namespace="default")
    pod_sandbox_config = api_pb2.PodSandboxConfig(
        metadata=sandbox_metadata, hostname="sandbox-host",
        log_directory="/var/log/pods", dns_config=api_pb2.DNSConfig(servers=["8.8.8.8", "8.8.4.4"]),
        linux=api_pb2.LinuxPodSandboxConfig(),
    )

    pod_request = api_pb2.RunPodSandboxRequest(config=pod_sandbox_config)
    pod_id = runtime_stub.RunPodSandbox(pod_request).pod_sandbox_id

    if not pod_id:
        raise RuntimeError("Error: No se pudo crear el PodSandbox.")

    print(f"PodSandbox creado con ID: {pod_id}")

    # Crear contenedor dentro del PodSandbox
    container_metadata = api_pb2.ContainerMetadata(name="container")
    container_config = api_pb2.ContainerConfig(
        metadata=container_metadata, image=api_pb2.ImageSpec(image=image_name),
        command=["/bin/sh", "-c", "while true; do echo 'Running...'; sleep 10; done"],
        linux=api_pb2.LinuxContainerConfig(),
    )

    container_request = api_pb2.CreateContainerRequest(
        pod_sandbox_id=pod_id, config=container_config, sandbox_config=pod_sandbox_config
    )
    container_id = runtime_stub.CreateContainer(container_request).container_id

    if not container_id:
        raise RuntimeError("Error: No se pudo crear el contenedor.")

    print(f"Contenedor creado con ID: {container_id}")

    # Iniciar contenedor
    runtime_stub.StartContainer(api_pb2.StartContainerRequest(container_id=container_id))
    print("Contenedor en ejecución.")
    return container_id

# Función para detener un contenedor
def stop_container(container_id):
    try:
        runtime_stub.StopContainer(api_pb2.StopContainerRequest(container_id=container_id))
        print(f"Contenedor {container_id} detenido.")
    except grpc.RpcError as e:
        print(f"Error al detener el contenedor: {e.details()}")

# Función para eliminar un contenedor
def remove_container(container_id):
    try:
        runtime_stub.RemoveContainer(api_pb2.RemoveContainerRequest(container_id=container_id))
        print(f"Contenedor {container_id} eliminado.")
    except grpc.RpcError as e:
        print(f"Error al eliminar el contenedor: {e.details()}")

# Función para reiniciar un contenedor
def restart_container(container_id):
    stop_container(container_id)
    runtime_stub.StartContainer(api_pb2.StartContainerRequest(container_id=container_id))
    print(f"Contenedor {container_id} reiniciado.")

# Función para obtener logs de un contenedor
def get_logs(container_id):
    try:
        logs = runtime_stub.ContainerStatus(api_pb2.ContainerStatusRequest(container_id=container_id)).log_path
        print(f"Logs del contenedor {container_id}: {logs}")
    except grpc.RpcError as e:
        print(f"Error al obtener logs: {e.details()}")

# Función para mostrar el menú interactivo
def menu():
    while True:
        print("\nGestor de Contenedores en CRI-O")
        print("1. Crear un contenedor")
        print("2. Listar contenedores")
        print("3. Detener un contenedor")
        print("4. Eliminar un contenedor")
        print("5. Reiniciar un contenedor")
        print("6. Obtener logs de un contenedor")
        print("7. Salir")

        opcion = input("Elige una opción: ")

        if opcion == "1":
            create_container()
        elif opcion == "2":
            list_containers()
        elif opcion == "3":
            container_id = input("Introduce el ID del contenedor a detener: ")
            stop_container(container_id)
        elif opcion == "4":
            container_id = input("Introduce el ID del contenedor a eliminar: ")
            remove_container(container_id)
        elif opcion == "5":
            container_id = input("Introduce el ID del contenedor a reiniciar: ")
            restart_container(container_id)
        elif opcion == "6":
            container_id = input("Introduce el ID del contenedor para obtener logs: ")
            get_logs(container_id)
        elif opcion == "7":
            print("Saliendo del gestor...")
            break
        else:
            print("Opción no válida. Intenta de nuevo.")

# Ejecutar el menú interactivo
if __name__ == "__main__":
    menu()
