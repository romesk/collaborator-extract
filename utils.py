
class LoginException(Exception):
    def __str__(self):
        return "Unable to login. Please check your credentials and try again."
