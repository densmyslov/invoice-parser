
# This file contains all the text labels used in the app
import streamlit as st

submit_button_label = {
    'us': 'Submit',
    'cn': '提交',
    'es': 'Enviar',
    'fr': 'Soumettre',
}

# SIGN UP PAGE AT 04_sign-up.py
account_setup_dict = {
    '1st message':{
        "us": "Don't have an account yet? Sign up now!",
        "cn": "还没有帐户？现在注册！",
        "es": "¿No tienes una cuenta todavía? ¡Regístrate ahora!",
        "fr": "Vous n'avez pas encore de compte? Inscrivez-vous maintenant!"
    },
    '2nd message':{
        "us": "A link to your account has been sent to your email address. Please check your email and click the link to activate your account.",
        "cn": "帐户的链接已发送到您的电子邮件地址。 请检查您的电子邮件并单击链接以激活帐户。",
        "es": "Se ha enviado un enlace a su cuenta a su dirección de correo electrónico. Por favor, compruebe su correo electrónico y haga clic en el enlace para activar su cuenta.",
        "fr": "Un lien vers votre compte a été envoyé à votre adresse e-mail. Veuillez vérifier votre e-mail et cliquer sur le lien pour activer votre compte." 
                  },
    'success_message':{
        "us": "Success ! Your account has been activated",
        "cn": "成功！您的帐户已激活",
        "es": "¡Éxito! Su cuenta ha sido activada",
        "fr": "Succès ! Votre compte a été activé"
    },
    'error message':{
        "us": "The confirmation code is invalid or expired. Please try again.",
        "cn": "确认码无效或已过期。 请再试一次。",
        "es": "El código de confirmación no es válido o ha caducado. Por favor, inténtelo de nuevo.",
        "fr": "Le code de confirmation n'est pas valide ou a expiré. Veuillez réessayer."
    },
    'password_error': {
        "us": "Your password does not meet the requirements. Please check the password requirements and try again.",
        "cn": "您的密码不符合要求。 请检查密码要求，然后重试。",
        "es": "Su contraseña no cumple con los requisitos. Por favor, compruebe los requisitos de la contraseña y vuelva a intentarlo.",
        "fr": "Votre mot de passe ne répond pas aux exigences. Veuillez vérifier les exigences du mot de passe et réessayer."
    },
    'password_error1': {
        "us": "We could not reset your password. Please try again.",
        "cn": "我们无法重置您的密码。 请再试一次。",
        "es": "No pudimos restablecer su contraseña. Por favor, inténtelo de nuevo.",
        "fr": "Nous n'avons pas pu réinitialiser votre mot de passe. Veuillez réessayer."
    },
    'email_exists_error': {
        "us": "This email address is already registered. Please try again with a different email address.\
                If you have forgotten your password, please got to 'settings' to reset your password.",
        "cn": "此电子邮件地址已注册。 请使用其他电子邮件地址再试一次。 如果您忘记了密码，请转到“设置”以重置密码。",
        "es": "Esta dirección de correo electrónico ya está registrada. Por favor, inténtelo de nuevo con una dirección de correo electrónico diferente.\
                Si ha olvidado su contraseña, por favor vaya a 'configuración' para restablecer su contraseña.",
        "fr": "Cette adresse e-mail est déjà enregistrée. Veuillez réessayer avec une adresse e-mail différente.\
        Si vous avez oublié votre mot de passe, veuillez vous rendre dans les 'settings' pour réinitialiser votre mot de passe."
    },
    'email_not_exists_error_0': {
        "us": "This email address is not registered. Please try again with a different email address.",
        "cn": "此电子邮件地址未注册。 请使用其他电子邮件地址再试一次。",
        "es": "Esta dirección de correo electrónico no está registrada. Por favor, inténtelo de nuevo con una dirección de correo electrónico diferente.",
        "fr": "Cette adresse e-mail n'est pas enregistrée. Veuillez réessayer avec une adresse e-mail différente."
    },
        
    'sign_up_form_0':
    {
    "us": "Please fill out the form below to sign up for a new account:",
    "cn": "请填写下面的表格以注册新帐户：",
    "es": "Por favor, rellene el siguiente formulario para registrarse en una nueva cuenta:",
    "fr": "Veuillez remplir le formulaire ci-dessous pour vous inscrire à un nouveau compte:"
    },
    'sign_up_form_1':
    {
    "us": "email address",
    "cn": "电子邮件地址",
    "es": "dirección de correo electrónico",
    "fr": "adresse e-mail"
    },
    'sign_up_form_2':
    {
    "us": "password",
    "cn": "密码",
    "es": "contraseña",
    "fr": "mot de passe"
    },
    'sign_up_form_3':
    {
    "us": "First Name",
    "cn": "名字",
    "es": "Nombre",
    "fr": "Prénom"
    },
    'sign_up_form_4':
    {
    "us": "Last Name",
    "cn": "姓",
    "es": "Apellido",
    "fr": "Nom de famille"
    },
    'sign_up_form_5':
    {
    "us": "Your country",
    "cn": "你的国家",
    "es": "Tu país",
    "fr": "Votre pays"
    },
    'confirm_email_form_0':
    {
    "us": "Please enter the confirmation code sent to your email address. \
        If you don't see the email, please check your spam folder.",
    "cn": "请输入发送到您的电子邮件地址的确认码。 如果您没有看到电子邮件，请检查垃圾邮件文件夹。",
    "es": "Por favor, introduzca el código de confirmación enviado a su dirección de correo electrónico. \
        Si no ve el correo electrónico, por favor revise su carpeta de spam.",
    "fr": "Veuillez saisir le code de confirmation envoyé à votre adresse e-mail. \
        Si vous ne voyez pas l'e-mail, veuillez vérifier votre dossier de spam."
    },
    'confirm_email_form_1':
    {
    "us": "Confirmation code",
    "cn": "确认码",
    "es": "Código de confirmación",
    "fr": "Code de confirmation"
    },
    
    'confirm_email_form_2':
    {
    "us": "Re-send confirmation code",
    "cn": "重新发送确认码",
    "es": "Reenviar código de confirmación",
    "fr": "Renvoyer le code de confirmation"
    },

    'password_specs_0':
    {
    "us": "Your password must meet the following requirements:",
    "cn": "您的密码必须符合以下要求：",
    "es": "Su contraseña debe cumplir los siguientes requisitos:",
    "fr": "Votre mot de passe doit répondre aux exigences suivantes:"
    },
    'password_specs_1':
    {
    "us": "1. Be at least 8 characters in length.",
    "cn": "1. 至少8个字符。",
    "es": "1. Tener al menos 8 caracteres de longitud.",
    "fr": "1. Avoir au moins 8 caractères de longueur."
    },
    'password_specs_2':
    {
    "us": "2. Contain only Latin characters (A-Z, a-z).",
    "cn": "2. 仅包含拉丁字符（A-Z，a-z）。",
    "es": "2. Contener sólo caracteres latinos (A-Z, a-z).",
    "fr": "2. Ne contenir que des caractères latins (A-Z, a-z)."
    },
    'password_specs_3':
    {
    "us": "3. Include at least one uppercase letter (A-Z).",
    "cn": "3. 包含至少一个大写字母（A-Z）。",
    "es": "3. Incluir al menos una letra mayúscula (A-Z).",
    "fr": "3. Inclure au moins une lettre majuscule (A-Z)."
    },
    'password_specs_4':
    {
    "us": "4. Include at least one lowercase letter (a-z).",
    "cn": "4. 包含至少一个小写字母（a-z）。",
    "es": "4. Incluir al menos una letra minúscula (a-z).",
    "fr": "4. Inclure au moins une lettre minuscule (a-z)."
    },

    'password_specs_5':
    {
    "us": "3. Contain at least one number (0-9).",
    "cn": "3. 至少包含一个数字（0-9）。",
    "es": "3. Contener al menos un número (0-9).",
    "fr": "3. Contenir au moins un nombre (0-9)."
    },
    'password_specs_5':
    {
    "us": "4. Include at least one special character (!@#$%^&*())",
    "cn": "4. 包含至少一个特殊字符（！@＃$％^＆*（））",
    "es": "4. Incluir al menos un carácter especial (!@#$%^&*())",
    "fr": "4. Inclure au moins un caractère spécial (!@#$%^&*())"
    },

    'forgot_password_message_0':
    {
        "us": "Forgot your password?",
        "cn": "忘记密码？",
        "es": "¿Olvidaste tu contraseña?",
        "fr": "Mot de passe oublié?"
    },
    'forgot_password_message_1':
    {
    "us": "If you forgot your password, please enter your email address and we will send you a confirmation code\
    if your email address is registered with us.",
    "cn": "如果您忘记了密码，请输入您的电子邮件地址，我们将向您发送确认码，\
    如果您的电子邮件地址已在我们这里注册。",
    "es": "Si olvidó su contraseña, ingrese su dirección de correo electrónico y le enviaremos un código de confirmación\
    si su dirección de correo electrónico está registrada con nosotros.",
    "fr": "Si vous avez oublié votre mot de passe, veuillez saisir votre adresse e-mail et nous vous enverrons un code de confirmation\
    si votre adresse e-mail est enregistrée chez nous."
    },
    'forgot_password_message_2':
    {
    "us": "Enter your new password",
    "cn": "输入新密码",
    "es": "Ingrese su nueva contraseña",
    "fr": "Entrez votre nouveau mot de passe"
    },
    'delete_account_message_0':
    {
    "us": "Delete your account",
    "cn": "删除您的帐户",
    "es": "Eliminar su cuenta",
    "fr": "Supprimer votre compte"
    },
    'delete_account_message_1':
    {
    "us": "You need to be signed in to delete your account, and the account you are deleting \
        must be the same as the one you are signed in with.",
    "cn": "您需要登录才能删除您的帐户，而您要删除的帐户\
        必须与您登录的帐户相同。",
    "es": "Debe iniciar sesión para eliminar su cuenta y la cuenta que está eliminando\
        debe ser la misma que la que inició sesión.",
    "fr": "Vous devez être connecté pour supprimer votre compte et le compte que vous supprimez\
        doit être le même que celui avec lequel vous êtes connecté."
    },
    'delete_account_message_2':
    {
    "us": "If you delete your account, you will lose all your data and you will not be able to recover it.",
    "cn": "如果您删除帐户，您将丢失所有数据，无法恢复。",
    "es": "Si elimina su cuenta, perderá todos sus datos y no podrá recuperarlos.",
    "fr": "Si vous supprimez votre compte, vous perdrez toutes vos données et vous ne pourrez pas les récupérer."
    },
    'delete_account_message_3':
    {
    "us": "If you still want to delete your account, please enter your email below.",
    "cn": "如果您仍然想删除您的帐户，请在下面输入您的电子邮件。",
    "es": "Si aún desea eliminar su cuenta, ingrese su correo electrónico a continuación.",
    "fr": "Si vous souhaitez toujours supprimer votre compte, veuillez saisir votre e-mail ci-dessous."
    },
    'delete_account_message_4':
    {
    "us": "Email address does not match with the one you are signed in with.",
    "cn": "电子邮件地址与您登录的电子邮件地址不匹配。",
    "es": "La dirección de correo electrónico no coincide con la que inició sesión.",
    "fr": "L'adresse e-mail ne correspond pas à celle avec laquelle vous êtes connecté."
    },
    'delete_account_message_5':
    {
    "us": "Your account has been deleted.",
    "cn": "您的帐户已被删除。",
    "es": "Su cuenta ha sido eliminada.",
    "fr": "Votre compte a été supprimé."
    },
    'delete_account_message_6':
    {
    "us": "We do not have an account with that email address. Please sign up first.",
    "cn": "我们没有使用该电子邮件地址的帐户。请先注册。",
    "es": "No tenemos una cuenta con esa dirección de correo electrónico. Por favor regístrese primero.",
    "fr": "Nous n'avons pas de compte avec cette adresse e-mail. Veuillez d'abord vous inscrire."
    },




}
st.cache_data()
def get_step_header_for_(header_text, color_dict):
    color=color_dict['header_color']

    header_html = f'''
        <style>
            .header {{
                font-size: 24px;
                font-weight: 600;
                color: {color};
            }}
        </style>
        <div class="header">{header_text}</div>
    '''
    st.markdown(header_html, unsafe_allow_html=True)

labels = {
            # ENGLISH:
            "us" : {
                "Amazon.com": 
                            {
                                "Step0": {
                                    "step_header" : "Step 0: Read the instructions below",
                                    "caption0" : "You need to have a Seller's account at Amazon.com or Walmart.com",
                                    "caption1" : "You don't need to sign-up to steps2profit.com to implement Steps 1-4 \
                                    while steps 5 and 6 require you to sign-up to steps2profit.com",
                                },
                                "Step1": {
                                    "step_header" : "Step 1: create table with products to add to your catalogue"
                                },
                                "Step2": {
                                    "step_header" : f"Step 2: Download file to add to your Amazon.com Seller's catalogue"
                                },
                                "Step3": {
                                    "step_header" : f"Step 3: Upload file to your Amazon.com Seller Central"
                                },
                                "Step4": {
                                    "step_header" : f"Step 4: Download 'amazon_file_loader-processing-summary.xslx' from Amazon Seller Central"
                            },
                            "Step5": {
                                "step_header" : "Step 5: Upload 'amazon_file_loader-processing-summary.xslx' to your account at Steps2Profit.com",
                                "caption0" : "To proceed with Step 5 you need to sign-up to Step2profit.com. If you are already subscribed,\
                                you need to login.",
                                "caption1" : "- Login to your account at Steps2Profit.com",
                                "caption2": "- Click on 'Expand to Step 5",
                                "caption3": "- Find  'amazon_file_loader-processing-summary.xslx' which you downloaded \
                                    from your Amazon Seller Central account.",
                                "caption4": "- Upload the file by using Copy/Paste option or by clicking on 'Browse Files' button"
                            }
                            },

                "Walmart.com" : {
                    "Step0": {
                        "step_header" : "Step 0: Read the instructions below",
                                    "caption0" : "You need to have a Seller's account at Amazon.com or Walmart.com",
                                    "caption1" : "You don't need to sign-up to steps2profit.com to implement Steps 1-4 \
                                    while steps 5 and 6 require you to sign-up to steps2profit.com",
                    },
                    "Step1": {
                        "step_header" : "Step 1: create table with products to add to your catalogue"
                    },
                    "Step2": {
                        "step_header" : f"Step 2: Download file to add to your Walmart.com Seller's catalogue"
                    },
                    "Step3": {
                        "step_header" : f"Step 3: Upload file to your Walmart.com Seller Central"
                    },
                    "Step4": {
                        "step_header" : f"Step 4: Export your catalog items from Walmart Seller Center"
                    },
                    "Step5": {
                        "step_header" : "Step 5: Upload 'manage_items.csv' to your account at Steps2Profit.com",
                        "caption0" : "To proceed with Step 5 you need to sign-up to Step2profit.com. If you are already subscribed,\
                                you need to login.",
                                "caption1" : "- Login to your account at Steps2Profit.com",
                                "caption2": "- Click on 'Expand to Step 5",
                                "caption3": "- Find  'manage_items.csv' which you exported from your Walmart Seller Central account.",
                                "caption4": "- Upload the file by using Copy/Paste option or by clicking on 'Browse Files' button"
                    }


                }
            },



            # CHINESE:
            "cn" : {
                "Amazon.com":
                            {
                                "Step0": {
                                    "step_header" : "第 0 步：閱讀下面的說明",
                                    "caption0" : "您需要擁有 Amazon.com 或 Walmart.com 的賣家帳戶",
                                    "caption1" : "您不需要註冊步驟2利潤.com，以實施步驟 1-4，而步驟 5 和 6 需要您註冊步驟2利潤.com",

                                },
                                "Step1": {
                                    "step_header" : "第 1 步：創建表格，將產品添加到您的目錄中"
                                },
                                "Step2": {
                                    "step_header" : f"第 2 步：下載文件以將其添加到您的 Amazon.com 賣家目錄中"
                                },
                                "Step3": {
                                    "step_header" : f"第 3 步：將文件上傳到您的 Amazon.com 賣家中心"
                                },
                                "Step4": {
                                    "step_header" : f"第 4 步：從 Amazon 賣家中心下載 'amazon_file_loader-processing-summary.xslx'"
                                },
                                "Step5": {
                                    "step_header" : "第 5 步：將 'amazon_file_loader-processing-summary.xslx 上傳到 Steps2Profit.com 上的帳戶",
                                    "caption0" : "要繼續進行第 5 步，您需要註冊 Steps2profit.com。 如果您已經訂閱，則需要登錄。",
                                    "caption1" : "- 登錄 Steps2Profit.com 帳戶",
                                    "caption2": "- 點擊 '展開到第 5 步'",
                                    "caption3": "- 找到從您的 Amazon 賣家中心帳戶下載的 'amazon_file_loader-processing-summary.xslx'",
                                    "caption4": "- 使用複製/粘貼選項或點擊 '瀏覽文件' 按鈕上傳文件"
                                }
                            },
                "Walmart.com" : {
                    "Step0": {
                        "step_header" : "第 0 步：閱讀下面的說明",
                        "caption0" : "您需要擁有 Amazon.com 或 Walmart.com 的賣家帳戶",
                        "caption1" : "您不需要註冊步驟2利潤.com，以實施步驟 1-4，而步驟 5 和 6 需要您註冊步驟2利潤.com",


                    },
                    "Step1": {
                        "step_header" : "第 1 步：創建表格，將產品添加到您的目錄中"
                    },
                    "Step2": {
                        "step_header" : f"第 2 步：下載文件以將其添加到您的 Walmart.com 賣家目錄中"
                    },
                    "Step3": {
                        "step_header" : f"第 3 步：將文件上傳到您的 Walmart.com 賣家中心"
                    },
                    "Step4": {
                        "step_header" : f"第 4 步：從 Walmart 賣家中心導出您的目錄項目"
                    },
                    "Step5": {
                        "step_header" : "第 5 步：將 'walmart_file_loader-processing-summary.xslx 上傳到 Steps2Profit.com 上的帳戶",
                        "caption0" : "要繼續進行第 5 步，您需要註冊 Steps2profit.com。 如果您已經訂閱，則需要登錄。",
                        "caption1" : "- 登錄 Steps2Profit.com 帳戶",
                        "caption2": "- 點擊 '展開到第 5 步'",
                        "caption3": "- 找到從您的 Walmart 賣家中心帳戶下載的 'walmart_file_loader-processing-summary.xslx'",
                        "caption4": "- 使用複製/粘貼選項或點擊 '瀏覽文件' 按鈕上傳文件"
                        
                    }
                }
            },

        # SPANISH:
        "es" : {
            "Amazon.com":
                        {
                    "Step0": {
                        "step_header" : "Paso 0: Lea las instrucciones a continuación",
                        "caption0" : "Necesita tener una cuenta de vendedor de Amazon.com o Walmart.com",
                        "caption1" : "No necesita registrarse en Steps2Profit.com para implementar los pasos 1-4, pero necesita registrarse para los pasos 5 y 6",

                    },
                    "Step1": {
                        "step_header" : "Paso 1: cree una tabla con productos para agregar a su catálogo"
                    },
                    "Step2": {
                        "step_header" : f"Paso 2: Descargue el archivo para agregarlo a su catálogo de vendedores de Amazon.com"
                    },
                    "Step3": {
                        "step_header" : f"Paso 3: Sube el archivo a tu centro de vendedores de Amazon.com"
                    },
                    "Step4": {
                        "step_header" : f"Paso 4: Descargue 'amazon_file_loader-processing-summary.xslx' de Amazon Seller Central"
                    },
                    "Step5": {
                        "step_header" : "Paso 5: Sube 'amazon_file_loader-processing-summary.xslx' a tu cuenta en Steps2Profit.com",
                        "caption0" : "Para continuar con el Paso 5, debe registrarse en Steps2profit.com. Si ya está suscrito, debe iniciar sesión.",
                        "caption1" : "- Inicie sesión en su cuenta en Steps2Profit.com",
                        "caption2": "- Haga clic en 'Expandir a Paso 5'",
                        "caption3": "- Encuentre 'amazon_file_loader-processing-summary.xslx' que descargó de su cuenta de Amazon Seller Central.",
                        "caption4": "- Sube el archivo usando la opción Copiar / Pegar o haciendo clic en el botón 'Examinar archivos'"

                    }
            },
            "Walmart.com" : {
                "Step0": {
                    "step_header" : "Paso 0: Lea las instrucciones a continuación",
                    "caption0" : "Necesita tener una cuenta de vendedor de Amazon.com o Walmart.com",
                    "caption1" : "No necesita registrarse en Steps2Profit.com para implementar los pasos 1-4, pero necesita registrarse para los pasos 5 y 6",

                },
                "Step1": {
                    "step_header" : "Paso 1: cree una tabla con productos para agregar a su catálogo"
                },
                "Step2": {
                    "step_header" : f"Paso 2: Descargue el archivo para agregarlo a su catálogo de vendedores de Walmart.com"
                },
                "Step3": {
                    "step_header" : f"Paso 3: Sube el archivo a tu centro de vendedores de Walmart.com"
                },
                "Step4": {
                    "step_header" : f"Paso 4: Exporte sus elementos de catálogo desde el centro de vendedores de Walmart"
                },
                "Step5": {
                    "step_header" : "Paso 5: Sube 'walmart_file_loader-processing-summary.xslx' a tu cuenta en Steps2Profit.com",
                    "caption0" : "Para continuar con el paso 5, debe registrarse en Steps2profit.com. Si ya está suscrito, debe iniciar sesión.",
                    "caption1" : "- Inicie sesión en su cuenta de Steps2Profit.com",
                    "caption2": "- Haga clic en 'Expandir al paso 5'",
                    "caption3": "- Busque el archivo 'walmart_file_loader-processing-summary.xslx' que descargó de su cuenta de Walmart Seller Center",
                    "caption4": "- Utilice la opción de copiar / pegar o haga clic en el botón 'Examinar archivos' para cargar el archivo"


                }

            }
        },
        "fr" : {
            "Amazon.com":
                        {
                    "Step0": {
                        "step_header" : "Étape 0: Lisez les instructions ci-dessous",
                        "caption0" : "Vous devez avoir un compte vendeur Amazon.com ou Walmart.com",
                        "caption1" : "Vous n'avez pas besoin de vous inscrire sur Steps2Profit.com pour mettre en œuvre les étapes 1-4, mais vous devez vous inscrire pour les étapes 5 et 6",

                    },
                    "Step1": {
                        "step_header" : "Étape 1: créez un tableau avec des produits à ajouter à votre catalogue"
                    },
                    "Step2": {
                        "step_header" : f"Étape 2: Téléchargez le fichier pour l'ajouter à votre catalogue de vendeurs Amazon.com"
                    },
                    "Step3": {
                        "step_header" : f"Étape 3: Téléchargez le fichier dans votre centre de vendeurs Amazon.com"
                    },
                    "Step4": {
                        "step_header" : f"Étape 4: Téléchargez 'amazon_file_loader-processing-summary.xslx' de Amazon Seller Central"
                    },
                    "Step5": {
                        "step_header" : "Étape 5: Téléchargez 'amazon_file_loader-processing-summary.xslx' dans votre compte Steps2Profit.com",
                        "caption0" : "Pour continuer à l'étape 5, vous devez vous inscrire sur Steps2profit.com. Si vous êtes déjà abonné, vous devez vous connecter.",
                        "caption1" : "- Connectez-vous à votre compte Steps2Profit.com",
                        "caption2": "- Cliquez sur 'Développer à l'étape 5'",
                        "caption3": "- Trouvez 'amazon_file_loader-processing-summary.xslx' que vous avez téléchargé de votre compte Amazon Seller Central.",
                        "caption4": "- Téléchargez le fichier en utilisant l'option Copier / Coller ou en cliquant sur le bouton 'Parcourir les fichiers'"


                    }
            },
            "Walmart.com" : {
                "Step0": {
                    "step_header" : "Étape 0: Lisez les instructions ci-dessous",
                    "caption0" : "Vous devez avoir un compte vendeur Amazon.com ou Walmart.com",
                    "caption1" : "Vous n'avez pas besoin de vous inscrire sur Steps2Profit.com pour mettre en œuvre les étapes 1-4, mais vous devez vous inscrire pour les étapes 5 et 6",

                },
                "Step1": {
                    "step_header" : "Étape 1: créez un tableau avec des produits à ajouter à votre catalogue"
                },
                "Step2": {
                    "step_header" : f"Étape 2: Téléchargez le fichier pour l'ajouter à votre catalogue de vendeurs Walmart.com"
                },
                "Step3": {
                    "step_header" : f"Étape 3: Téléchargez le fichier dans votre centre de vendeurs Walmart.com"
                },
                "Step4": {
                    "step_header" : f"Étape 4: Téléchargez 'walmart_file_loader-processing-summary.xslx' de Walmart Seller Center"
                },
                "Step5": {
                    "step_header" : "Étape 5: Téléchargez 'walmart_file_loader-processing-summary.xslx' dans votre compte Steps2Profit.com",
                    "caption0" : "Pour continuer à l'étape 5, vous devez vous inscrire sur Steps2profit.com. Si vous êtes déjà abonné, vous devez vous connecter.",
                    "caption1" : "- Connectez-vous à votre compte Steps2Profit.com",
                    "caption2": "- Cliquez sur 'Développer à l'étape 5'",
                    "caption3": "- Trouvez 'walmart_file_loader-processing-summary.xslx' que vous avez téléchargé de votre compte Walmart Seller Center.",
                    "caption4": "- Téléchargez le fichier en utilisant l'option Copier / Coller ou en cliquant sur le bouton 'Parcourir les fichiers'"

                }

            }
        },
    }

page_header_dict = {
    "us": "No theories here - if you make money, so do we.",
    "cn": "没有理论-如果你赚钱，我们也会赚钱。",
    "es": "Sin teorías aquí - si ganas dinero, nosotros también ganamos dinero.",
    "fr": "Sans théories ici - si vous gagnez de l'argent, nous gagnons aussi de l'argent."
}

