import efficient_det_model

def test_model():
    model = efficient_det_model.create_model()

def test_load_model():
    model = efficient_det_model.load_model()

if __name__ == "__main__":
    test_model()
    test_load_model()