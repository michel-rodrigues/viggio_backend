import os


def from_environment(request):
    env = os.environ.get('ENVIRONMENT')
    return {
        'ENVIRONMENT': env,
        'ENVIRONMENT_COLOR': 'red' if env == 'production' else 'grey',
    }
