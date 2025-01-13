use env_logger;
use log::{debug, info};
use serde::Deserialize;
use std::env;
use std::sync::{Arc, Mutex};
use zenoh::{key_expr::KeyExpr, Config};

#[derive(Debug, Deserialize, Clone)]
struct TopicPair {
    input: String,
    output: String,
}

#[derive(Debug, Deserialize, Clone)]
struct Process {
    id: String,
    control_topic: String,
}

#[derive(Debug, Deserialize, Clone)]
struct Topics {
    process: Process,
    topics: Vec<TopicPair>,
}

#[tokio::main]
async fn main() {
    // Initialize the logger
    env_logger::init();

    // Read environment variables
    let process_id = env::var("PROCESS_ID").expect("PROCESS_ID not set");
    let control_topic_base = env::var("CONTROL_TOPIC_BASE").expect("CONTROL_TOPIC_BASE not set");
    let topics_env = env::var("TOPICS").expect("TOPICS not set");

    // Parse the topics from the environment variable
    let topic_pairs: Vec<TopicPair> = topics_env
        .split(',')
        .map(|pair| {
            let mut parts = pair.split(':');
            TopicPair {
                input: parts.next().unwrap().to_string(),
                output: parts.next().unwrap().to_string(),
            }
        })
        .collect();

    // Create the Topics struct using the environment variables
    let topics = Topics {
        process: Process {
            id: process_id,
            control_topic: control_topic_base,
        },
        topics: topic_pairs,
    };

    // Log the topics
    debug!("Parsed topics: {:?}", topics);

    // Initialize logging
    zenoh::init_log_from_env_or("error");

    // Create a zenoh session
    let session = zenoh::open(Config::default()).await.unwrap();
    info!("Zenoh session created");

    // Shared state for topics
    let topics = Arc::new(Mutex::new(topics));

    // Loop for the topics
    for topic in topics.lock().unwrap().topics.clone() {
        let input = topic.input.clone();
        let output = topic.output.clone();
        let session = session.clone();

        tokio::spawn(async move {
            // Convert the input and output to KeyExpr
            let input = KeyExpr::try_from(input.as_str()).unwrap();
            let output = KeyExpr::try_from(output.as_str()).unwrap();
            debug!("Created KeyExpr for input: {:?}, output: {:?}", input, output);

            // Create a subscriber
            let subscriber = session.declare_subscriber(&input).await.unwrap();
            debug!("Declared subscriber for {:?}", input);

            // Create a publisher
            let publisher = session.declare_publisher(&output).await.unwrap();
            debug!("Declared publisher for {:?}", output);

            // Handle incoming messages and forward them to the output topic
            while let Ok(sample) = subscriber.recv_async().await {
                let payload = sample.payload().to_bytes();
                publisher.put(payload).await.unwrap();
                info!("Forwarded message from {:?} to {:?}", input, output);
            }
        });
    }

    // Create a subscriber for configuration updates
    let id = topics.lock().unwrap().process.id.clone();
    let control_topic = format!("{}{}", topics.lock().unwrap().process.control_topic, id);
    print!("control_topic: {:?}", control_topic);
    let control_key = KeyExpr::try_from(control_topic.as_str()).unwrap();
    let config_subscriber = session.declare_subscriber(&control_key).await.unwrap();
    info!("Declared subscriber for configuration and control on {:?}", control_key);

    // Handle incoming configuration updates
    while let Ok(sample) = config_subscriber.recv_async().await {
        let payload = sample.payload().to_bytes();
        debug!("Received configuration update: {:?}", payload);
    }

    // Keep the main task alive
    println!("Press CTRL-C to quit...");
    tokio::signal::ctrl_c().await.unwrap();
}