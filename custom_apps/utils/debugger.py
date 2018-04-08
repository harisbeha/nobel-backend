def setup():
    try:
        import googleclouddebugger
        googleclouddebugger.enable(version='v0.0.1', module='backend', project_id='nobel-weather-associates',
                                   project_number='419191605818',
                                   service_account_json_file='/app/google-cloud.json')
    except ImportError:
        pass
