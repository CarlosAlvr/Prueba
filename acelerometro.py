import time
import random
import zenoh

def main(conf: zenoh.Config):
    # Configurar sesión de Zenoh
    zenoh.init_log_from_env_or("error")

    #print("Opening session...")
    with zenoh.open(conf) as session:

        #print("Declaring Publisher on 'casa/persona1/acelerometro'...")
        pub = session.declare_publisher("casa/persona1/acelerometro")

        print("Publishing random accelerometer data every second...")
        try:
            while True:
                # Generar 0 o 1 con probabilidad 0.1 para 1
                value = 1 if random.random() < 0.3 else 0

                # Publicar el valor
                pub.put(str(value))
                if(value==1):
                    print(f"Published: {value}")

                # Esperar 1 segundo
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting...")

# --- Command line argument parsing --- --- --- --- --- ---
if __name__ == "__main__":
    import argparse
    import common

    parser = argparse.ArgumentParser(prog="random_accelerometer", description="Publish random accelerometer data.")
    common.add_config_arguments(parser)

    args = parser.parse_args()
    conf = common.get_config_from_args(args)

    main(conf)