import time
import zenoh
import os

DOCKER_IMAGE_ZIP = "imagen.zip"  # Nombre del archivo ZIP que contiene la carpeta con la imagen Docker

def main(conf: zenoh.Config):
    zenoh.init_log_from_env_or("error")

    print("Abriendo sesión Zenoh...")
    with zenoh.open(conf) as session:
        print("Declarando Publisher en 'distribuir/imagen_docker_zip'...")
        pub = session.declare_publisher("distribuir/imagen_docker_zip")

        print("Esperando nuevos nodos...")

        def listener_new_node(sample: zenoh.Sample):
            nodo_id = sample.payload.to_string()
            print(f"Nuevo nodo detectado: {nodo_id}. Preparando envío de la carpeta ZIP...")

            # Validar que el archivo ZIP existe
            if not os.path.exists(DOCKER_IMAGE_ZIP):
                print(f"Error: El archivo ZIP '{DOCKER_IMAGE_ZIP}' no existe.")
                return

            try:
                # Leer el archivo ZIP
                with open(DOCKER_IMAGE_ZIP, "rb") as docker_zip:
                    data = docker_zip.read()
               
                # Publicar el archivo ZIP
                pub.put(data)
                print(f"Archivo ZIP enviado al nodo: {nodo_id}")

            except Exception as e:
                print(f"Error enviando la carpeta ZIP: {e}")

        # Suscriptor para detección de nuevos nodos
        session.declare_subscriber("nodos/nuevo/**", listener_new_node)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Saliendo...")

if __name__ == "__main__":
    import argparse
    import common

    parser = argparse.ArgumentParser(description="Nodo maestro para distribuir una carpeta en formato ZIP.")
    common.add_config_arguments(parser)
    args = parser.parse_args()
    conf = common.get_config_from_args(args)
    main(conf)

if __name__ == "__main__":
    import argparse
    import common

    parser = argparse.ArgumentParser(description="Nodo maestro para distribuir una carpeta en formato ZIP.")
    common.add_config_arguments(parser)
    args = parser.parse_args()
    conf = common.get_config_from_args(args)
    main(conf)