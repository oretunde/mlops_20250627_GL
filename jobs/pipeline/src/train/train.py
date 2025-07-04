# General Comment 
import os
import io
import mlflow
import argparse
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.ensemble import GradientBoostingRegressor

def select_first_file(path):
    """Selects the first file in the folder under the assumption there is only one file in the folder.
    Args:
        path (str): path to the directory or file to choose
    Returns:
        str: full path of the selected file
    """
    files = os.listdir(path)
    return os.path.join(path, files[0])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_data", type=str, help="path to train data")
    parser.add_argument("--test_data", type=str, help="path to test data")
    parser.add_argument("--n_estimators", required=False, default=100, type=int)
    parser.add_argument("--learning_rate", required=False, default=0.1, type=float)
    parser.add_argument("--registered_model_name", type=str, help="model name")
    parser.add_argument("--model", type=str, help="path to model file")  # Add this if needed
    args = parser.parse_args()  # Parse the command-line arguments

    mlflow.start_run()  # Start a new MLflow run

    os.makedirs("./outputs", exist_ok=True)  # Create the "outputs" directory if it doesn't exist

    # Load data
    car_mpg_train = pd.read_csv(select_first_file(args.train_data))  # Read the training data
    car_mpg_test = pd.read_csv(select_first_file(args.test_data))  # Read the test data

    target = 'mpg'
    numeric_features = ['cyl', 'disp', 'hp', 'wt', 'acc', 'yr', 'origin', 'car_type']

    # Extract the features and target from the training and test data
    X_train = car_mpg_train.drop(columns=[target])
    y_train = car_mpg_train[target]
    X_test = car_mpg_test.drop(columns=[target])
    y_test = car_mpg_test[target]

    # Create a column transformer for preprocessing the numeric features
    preprocessor = make_column_transformer(
        (StandardScaler(), numeric_features)
    )

    # Create a Gradient Boosting Regressor model
    model_gbr = GradientBoostingRegressor(
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate
    )

    # Create a pipeline with preprocessing and the model
    model_pipeline = make_pipeline(preprocessor, model_gbr)

    # Train the model
    model_pipeline.fit(X_train, y_train)

    # Evaluate the model
    rmse = model_pipeline.score(X_test, y_test)
    mlflow.log_metric("RMSE", float(rmse))

    # Make predictions on the test data
    predictions = model_pipeline.predict(X_test)

    # Save predictions to a DataFrame
    prediction_df = pd.DataFrame({
        "Actual": y_test,
        "Predicted": predictions
    })

    # Save the in-memory CSV to a file and log it as an artifact
    with io.StringIO() as csv_buffer:
        prediction_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        artifact_path = "predictions.csv"
        with open(artifact_path, "w") as f:
            f.write(csv_buffer.getvalue())
        
        mlflow.log_artifact(artifact_path)

    # Register the model pipeline in MLflow
    mlflow.sklearn.log_model(
        sk_model=model_pipeline,
        registered_model_name=args.registered_model_name,
        artifact_path="gbr-car-mpg-predictor"
    )

    mlflow.end_run()

if __name__ == '__main__':
    main()






