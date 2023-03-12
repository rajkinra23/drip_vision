from confluent_kafka.admin import AdminClient

if __name__ == "__main__":
    admin_client = AdminClient({"bootstrap.servers": "localhost:9092"})
