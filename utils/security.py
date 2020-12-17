import os


class Security:
    """
    JWT Middle-ware
    """
    fernet_secret = os.environ['TOKEN_SECRET'].encode('utf-8')
    login_page_url = "http://user-service-dash.eba-y82cxuwr.us-east-2.elasticbeanstalk.com/"
    jwt_secret = os.environ['JWT_SECRET']
    jwt_algo = os.environ['JWT_ALGO']
    jwt_exp_delta_sec = float(os.environ['JWT_EXP'])
    dash_page_url = "http://dashboard-env-1.eba-szsfmavw.us-east-2.elasticbeanstalk.com/"
    user_page_url = 'http://user-service-dash.eba-y82cxuwr.us-east-2.elasticbeanstalk.com/users/'
