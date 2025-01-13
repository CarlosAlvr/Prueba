import os
import zenoh
import zipfile
import subprocess
import socket
import time

def main(conf: zenoh.Config):
    zenoh.init_log_from_env_or("error")

    print("Abriendo sesión Zenoh...")
    with zenoh.open(conf) as session:
        print("Declarando Publisher en 'nodos/nuevo' y Suscriptor en 'distribuir/imagen_docker_zip'...")

        # Suscribirse para recibir la imagen Docker ZIP
        def listener_image(sample: zenoh.Sample):
            print("Archivo ZIP recibido. Guardando en archivo temporal...")

            try:
                # Guardar el archivo ZIP
                data = sample.payload.to_bytes()
                print(f"Tamaño del archivo ZIP recibido: {len(data)} bytes")
                with open("imagen.zip", "wb") as f:
                    f.write(data)

                print("Desempaquetando archivo ZIP...")
                with zipfile.ZipFile("imagen.zip", "r") as zip_ref:
                    zip_ref.extractall("carpeta_extraida")  # Extraer todo en la carpeta "carpeta_extraida"

                # Ruta de la carpeta 'imagen' dentro del ZIP extraído
                imagen_docker_path = os.path.join("carpeta_extraida")

                if not os.path.exists(imagen_docker_path):
                    print(f"Error: No se encontró el archivo 'dockerfile' en el archivo ZIP")
                    return

                print(f"Carpeta 'dockerfile' encontrada: {imagen_docker_path}")
                
                
                # Aquí puedes realizar acciones con los archivos extraídos
                # Por ejemplo, procesar algún archivo específico o ejecutar comandos adicionales.

                if os.path.exists(imagen_docker_path):
                    print(f"Construyendo imagen Docker desde {imagen_docker_path}...")
                    subprocess.run(["docker", "build", "-t", imagen_docker_path, "carpeta_extraida"], check=True)
                    print("Imagen Docker construida correctamente.")

                    # Ejecutar la imagen Docker
                    print("Ejecutando la imagen Docker...")
                    subprocess.run(["docker", "run", "--rm", "nombre_de_la_imagen"], check=True)
                    print("Imagen Docker ejecutada correctamente.")
                else:
                    print(f"Error: No se encontró el archivo de imagen Docker en {imagen_docker_path}.")
                
                
                
                print("Todos los archivos en 'imagen' procesados correctamente.")

            except Exception as e:
                print(f"Error procesando el archivo ZIP: {e}")
        session.declare_subscriber("distribuir/imagen_docker_zip", listener_image)

        
        # Publicar notificación al maestro
        pub = session.declare_publisher("nodos/nuevo/video")
        nodo_id = socket.gethostname()  # Usa el nombre del host como identificación del nodo
        pub.put(nodo_id)
        print(f"Notificación enviada: Nuevo nodo disponible con ID '{nodo_id}'")

        print("Esperando imágenes Docker ZIP...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Saliendo...")

if __name__ == "__main__":
    import argparse
    import common

    parser = argparse.ArgumentParser(description="Nodo receptor para instalar imágenes Docker desde un ZIP.")
    common.add_config_arguments(parser)
    args = parser.parse_args()
    conf = common.get_config_from_args(args)
    main(conf)