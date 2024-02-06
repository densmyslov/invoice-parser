
from botocore.exceptions import ClientError
import hmac
import hashlib
import base64
import logging
import uuid

logger = logging.getLogger(__name__)


class CognitoIdentityProviderWrapper:
    """Encapsulates Amazon Cognito actions"""

    def __init__(self, cognito_idp_client, user_pool_id, client_id, client_secret=None):
        """
        :param cognito_idp_client: A Boto3 Amazon Cognito Identity Provider client.
        :param user_pool_id: The ID of an existing Amazon Cognito user pool.
        :param client_id: The ID of a client application registered with the user pool.
        :param client_secret: The client secret, if the client has a secret.
        """
        self.cognito_idp_client = cognito_idp_client
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.client_secret = client_secret

    def _secret_hash(self, username):
        """Computes the secret hash value required by certain Amazon Cognito API calls"""
        message = bytes(username + self.client_id, 'utf-8')
        secret = bytes(self.client_secret, 'utf-8')
        dig = hmac.new(secret, message, hashlib.sha256).digest()
        return base64.b64encode(dig).decode()

    def sign_up_user(self, given_name, family_name, email, password):
      """
      Signs up a new user with Amazon Cognito. This action prompts Amazon Cognito
      to send an email to the specified email address. The email contains a code that
      can be used to confirm the user.

      When the user already exists, the user status is checked to determine whether
      the user has been confirmed.

      :param given_name: The first name of the new user.
      :param family_name: The last name of the new user.
      :param email: The email address of the new user.
      :param locale: The locale of the new user.
      :param password: The password for the new user.
      :return: True when the user is already confirmed with Amazon Cognito.
              Otherwise, false.
      """
      try:
          username = str(uuid.uuid4())  # Generate a random UUID as the user name
          kwargs = {
              'ClientId': self.client_id,
              'Username': username,
              'Password': password,
              'UserAttributes': [
                  {'Name': 'given_name', 'Value': given_name},
                  {'Name': 'family_name', 'Value': family_name},
                  {'Name': 'email', 'Value': email}
                #   {'Name': 'locale', 'Value': locale}
              ]
          }
          if self.client_secret is not None:
              kwargs['SecretHash'] = self._secret_hash(username)
          response = self.cognito_idp_client.sign_up(**kwargs)
          # confirmed = response['UserConfirmed']
          confirmed = username
      except ClientError as err:
          if err.response['Error']['Code'] == 'UsernameExistsException':
              response = self.cognito_idp_client.admin_get_user(
                  UserPoolId=self.user_pool_id, Username=username)
              logger.warning("User %s exists and is %s.", username, response['UserStatus'])
              confirmed = response['UserStatus'] == 'CONFIRMED'
          else:
              logger.error(
                  "Couldn't sign up %s. Here's why: %s: %s", email,
                  err.response['Error']['Code'], err.response['Error']['Message'])
              raise
      return confirmed


    def confirm_user_sign_up(self, user_name, confirmation_code):
        """
        Confirms a previously created user. A user must be confirmed before they
        can sign in to Amazon Cognito.

        :param user_name: The name of the user to confirm.
        :param confirmation_code: The confirmation code sent to the user's registered
                                  email address.
        :return: True when the confirmation succeeds.
        """
        try:
            kwargs = {
                'ClientId': self.client_id, 'Username': user_name,
                'ConfirmationCode': confirmation_code}
            if self.client_secret is not None:
                kwargs['SecretHash'] = self._secret_hash(user_name)
            self.cognito_idp_client.confirm_sign_up(**kwargs)
        except ClientError as err:
            logger.error(
                "Couldn't confirm sign up for %s. Here's why: %s: %s", user_email,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return True

    def resend_confirmation(self, user_name):
        """
        Prompts Amazon Cognito to resend an email with a new confirmation code.

        :param user_name: The name of the user who will receive the email.
        :return: Delivery information about where the email is sent.
        """
        try:
            kwargs = {
                'ClientId': self.client_id, 'Username': user_name}
            if self.client_secret is not None:
                kwargs['SecretHash'] = self._secret_hash(user_name)
            response = self.cognito_idp_client.resend_confirmation_code(**kwargs)
            delivery = response['CodeDeliveryDetails']
        except ClientError as err:
            logger.error(
                "Couldn't resend confirmation to %s. Here's why: %s: %s", user_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return delivery

    def list_users(self):
      """
      Returns a list of the users in the current user pool.

      :return: The list of users.
      """
      try:
          response = self.cognito_idp_client.list_users(UserPoolId=self.user_pool_id)
          users = response['Users']
      except ClientError as err:
          logger.error(
              "Couldn't list users for %s. Here's why: %s: %s", self.user_pool_id,
              err.response['Error']['Code'], err.response['Error']['Message'])
          raise
      else:
          return users

    def sign_in_user(self, email, password):
        """
        Authenticates a user with Amazon Cognito using their email address and password.

        :param email: The email address of the user to authenticate.
        :param password: The password of the user to authenticate.
        :return: The access token for the authenticated user.
        """
        try:
            kwargs = {
                'ClientId': self.client_id,
                'AuthFlow': 'USER_PASSWORD_AUTH',
                'AuthParameters': {
                    'USERNAME': email,
                    'PASSWORD': password
                }
            }
            if self.client_secret is not None:
                kwargs['AuthParameters']['SECRET_HASH'] = self._secret_hash(email)
            response = self.cognito_idp_client.initiate_auth(**kwargs)
            authenticated = response['AuthenticationResult']['AccessToken']
            logger.info("User %s was successfully authenticated.", email)
        except ClientError as err:
            logger.error(
                "Couldn't authenticate user %s. Here's why: %s: %s", email,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        result = response['AuthenticationResult']
        access_token = result['AccessToken']
        refresh_token = result['RefreshToken']
        id_token = result['IdToken']

        return access_token, refresh_token, id_token

    def forgot_password(self, email):
        """
        Initiates a forgotten password flow for a user in a user pool.

        :param email: The email address of the user.
        :return: A dictionary containing information about the password reset request.
        """
        try:
            if self.client_secret is not None:
                secret_hash = self._secret_hash(email)
            else:
                secret_hash = None

            response = self.cognito_idp_client.forgot_password(
                ClientId=self.client_id,
                Username=email,
                SecretHash=secret_hash
            )
            return response
        except self.cognito_idp_client.exceptions.UserNotFoundException as e:
            raise Exception('User not found') from e
        except Exception as e:
            raise e

    def confirm_forgot_password(self, email, verification_code, new_password):
        """
        Confirms a forgotten password flow for a user in a user pool.

        :param email: The email address of the user.
        :param verification_code: The verification code sent to the user to confirm the password reset.
        :param new_password: The new password to set for the user.
        :return: A dictionary containing information about the updated user account.
        """
        try:
            if self.client_secret is not None:
                secret_hash = self._secret_hash(email)
            else:
                secret_hash = None

            response = self.cognito_idp_client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=email,
                ConfirmationCode=verification_code,
                Password=new_password,
                SecretHash=secret_hash
            )
            return response
        except self.cognito_idp_client.exceptions.UserNotFoundException as e:
            raise Exception('User not found') from e
        except Exception as e:
            raise e



