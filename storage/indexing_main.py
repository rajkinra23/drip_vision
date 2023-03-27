from storage import indexing_lib

if __name__ == "__main__":
    # Create indexer on the training directory
    indexer = indexing_lib.Indexer("/home/rajkinra23/git/drip_vision/data/embeddings_dataset/train/")

    # Run indexing
    indexer.run_indexing()