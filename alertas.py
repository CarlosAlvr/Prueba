import time
import zenoh

def main(conf: zenoh.Config):
    # Configurar sesión de Zenoh
    zenoh.init_log_from_env_or("error")

    print("Opening session...")
    with zenoh.open(conf) as session:

        print("Declaring Subscriber on 'casa/persona1/caida' and 'casa/habitacion1/video'...")
        print("Declaring Publisher on 'casa/alerta'...")
        pub_alert = session.declare_publisher("casa/alerta")

        caida_detected = False

        def listener_caida(sample: zenoh.Sample):
            nonlocal caida_detected
            #print(f"Received fall detection data on '{sample.key_expr}': {sample.payload.to_bytes()}")

            # Convertir el dato recibido a entero
            caida_value = int(sample.payload.to_bytes())

            if caida_value == 1:
                caida_detected = True
                print("Fall detected, waiting for recognition data...")

        def listener_recognition(sample: zenoh.Sample):
            nonlocal caida_detected

            print(f"Received recognition data on '{sample.key_expr}'")
            try:
                # Convertir los datos recibidos a un entero
                recognition_value = int(sample.payload.to_bytes().decode(errors='ignore').strip())

                if caida_detected:
                    if recognition_value == 1:
                        print("ALERT: Fall and recognition detected!")
                        pub_alert.put("1")
                    else:
                        print("No recognition detected. Resetting state.")
                        pub_alert.put("0")

                    caida_detected = False
            except Exception as e:
                print(f"Error processing recognition data: {e}")



        # Declarar los suscriptores
        session.declare_subscriber("casa/**/caida", listener_caida)
        session.declare_subscriber("casa/**/deteccion", listener_recognition)

        print("Listening for fall detection and recognition... Press CTRL-C to quit.")
        try:
            while True:
                time.sleep(1)  # Mantener el programa en ejecución
        except KeyboardInterrupt:
            print("Exiting...")

# --- Command line argument parsing --- --- --- --- --- ---
if __name__ == "__main__":
    import argparse
    import common

    parser = argparse.ArgumentParser(prog="alert_detection", description="Listen for fall detection and recognition to send alerts.")
    common.add_config_arguments(parser)

    args = parser.parse_args()
    conf = common.get_config_from_args(args)

    main(conf)
