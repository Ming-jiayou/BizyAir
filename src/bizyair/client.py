import json
import urllib.request
import urllib.error

__all__ = ["BizyAirRequestClient"]


class BaseClient:
    def __init__(self, api_url, api_key: str = None):
        self.api_url = api_url
        self.API_KEY: str = api_key

    def get_headers(self, sse=False):
        if self.API_KEY is None or not self.API_KEY.startswith("sk-"):
            raise ValueError(
                f"API key is not set. Please provide a valid API key(from cloud.siliconflow.cn), {self.API_KEY=}"
            )

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.API_KEY}",
        }

        if sse:
            headers["accept"] = "text/event-stream"

        return headers

    def _handle_url_error(self, e):
        error_message = str(e)
        if "Unauthorized" in error_message:
            raise Exception(
                "Key is invalid, please refer to https://cloud.siliconflow.cn to get the API key.\n"
                "If you have the key, please click the 'BizyAir Key' button at the bottom right to set the key."
            )
        else:
            raise Exception(
                f"Failed to connect to the server: {e}, if you have no key, "
            )


class BizyAirRequestClient(BaseClient):
    def __init__(self, api_url, workflow_api, api_key=None):
        super().__init__(api_url, api_key)
        self.workflow_api = workflow_api

    def send_request(self):
        try:
            data = json.dumps(self.workflow_api).encode("utf-8")
            req = urllib.request.Request(
                self.api_url, data=data, headers=self.get_headers(), method="POST"
            )
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
                return response_data
        except urllib.error.URLError as e:
            self._handle_url_error(e)


class BizyAirStreamClient(BaseClient):
    def __init__(self, api_url, workflow_api, api_key=None):
        super().__init__(api_url, api_key)
        self.workflow_api = workflow_api
        self.response = None

    def __enter__(self):
        data = json.dumps(self.workflow_api).encode("utf-8")
        req = urllib.request.Request(
            self.api_url, data=data, headers=self.get_headers(sse=True), method="POST"
        )
        self.response = urllib.request.urlopen(req)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.response:
            self.response.close()

    def events(self):
        try:
            for line in self.response:
                decoded_line = line.decode("utf-8")
                if decoded_line.startswith("data:"):
                    event_data = decoded_line[5:].strip()
                    yield event_data
        except GeneratorExit:
            self.close()

    def close(self):
        if self.response:
            self.response.close()


# Example usage
if __name__ == "__main__":
    api_url = "http://0.0.0.0:8000/supernode/test-dummy1"
    workflow_api = {"key1": "value1", "key2": "value2"}
    api_key = "YOUR_API_KEY"

    # Example for sending a POST request
    request_client = BizyAirRequestClient(api_url, workflow_api, api_key)
    try:
        response_data = request_client.send_request()
        print(f"Response Data: {response_data}")
    except Exception as e:
        print(e)

    # Example for SSE client using with statement
    try:
        with BizyAirStreamClient(api_url, workflow_api, api_key) as stream_client:
            for event_data in stream_client.events():
                print(f"Event Data: {event_data}")
    except Exception as e:
        print(e)
