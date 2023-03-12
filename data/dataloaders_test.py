# Unit test
import data_loaders

def test_adaptor():
    # Get the adaptor
    adaptor = data_loaders.DeepFashionDatasetAdaptor(data_loaders.TRAIN)

    # Assert sizes
    assert len(adaptor) == 191961
    
if __name__ == "__main__":
    test_adaptor()