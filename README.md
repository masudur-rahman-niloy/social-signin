### Configuration For Google Sign In:

1. If there is no project created earlier, then first create a project like the following image from Google API Console. Click on “New Project” from the right corner of this page. 

![Screenshot from 2021-07-17 08-05-04](https://user-images.githubusercontent.com/77866740/126026037-f77e9497-76cb-499b-9bca-e3b1b2ceca72.jpg)

1. Then you have to set a name for your project like as following image:

![Screenshot from 2021-07-17 08-05-32](https://user-images.githubusercontent.com/77866740/126026048-2416d1e0-c573-419f-b060-94e3a920d63f.jpg)

1. Then select that created project from the project list.
1. Then click on **Credentials**. Click on **Create Credentials** and choose "OAuth client ID."

![Screenshot from 2021-07-15 11-39-16](https://user-images.githubusercontent.com/77866740/126026073-e2508a0a-bac7-4712-8a22-b4e08f2cfa3d.jpg)
 
1. Then click on **Configure Consent Screen** like in the following image and then select **External** in consent screen and click on **Create** button.

![Screenshot from 2021-07-15 11-39-49](https://user-images.githubusercontent.com/77866740/126026083-1ec5e36b-d9ad-45dd-97b8-d7a078480478.jpg)


1. Then give **APP Name** and your email addresses in required fields and there is no need to configure any fields in this page and then click **Save and continue** for next two pages and then click on **Back to Dashboard** button.  

![Screenshot from 2021-07-15 11-40-28](https://user-images.githubusercontent.com/77866740/126026086-f28ec127-3834-4386-b851-e64dc705aadc.jpg)

1. After that again click on **Credentials** from the left side menu and then click on **Create Credentials** -> **OAuth Client Id**. Then you will get a dropdown. You have to select **Web Application** from that menu. Then you have to configure **Authorized JavaScript origins** and **Authorized redirect URIs by clicking** on **Add URI** button. Here I am showing localhost. When you want to add live links you can add those links here.

![test](https://user-images.githubusercontent.com/77866740/126026103-169bde0b-d8eb-46ca-9324-bc448b912ba0.jpg)

1. Then you will get **App client id** and **client secret id** here. Please save these ids for further use.

![Screenshot from 2021-07-17 08-42-21](https://user-images.githubusercontent.com/77866740/126026123-8e88978c-f952-458e-866c-124cdf24e26a.jpg)             

### Configuration For Facebook SIgn-in:

1. You have to go https://developers.facebook.com/apps/?show_reminder=true for creating apps on facebook.
Then click on **Create App** and then choose any option like in following image:

![Screenshot from 2021-07-17 09-23-04](https://user-images.githubusercontent.com/77866740/126026192-6c4ca995-89d4-4953-88d8-b295dbb26187.jpg)

1. Then click **Continue** and then give app name and create new app:

![Screenshot from 2021-07-17 09-23-17](https://user-images.githubusercontent.com/77866740/126026200-8343d5a6-eae5-49c2-8a39-aa9d47af3743.jpg)

1. Then select **Settings** -> **Basic**. Here you will get App Id and App secret Id, store them for further use.

1. You have to give your application domain name in **App Domains** and  a public link of your application in **Privacy Policy URL** and **Terms of Service URL**. I have configured localhost here. If you want to configure your application’s live link then you have to give the live URL here.

![Screenshot from 2021-07-17 09-41-43](https://user-images.githubusercontent.com/77866740/126026203-e7ce88ce-8a39-4bb9-a2ce-7647d25f833b.jpg)

1. Then click on **Add Platform** button and select **Website** from the option and then your application site url here. If you want to give your application’s  live link then you have to give it instead of the localhost link. 

![Screenshot from 2021-07-17 09-35-18](https://user-images.githubusercontent.com/77866740/126026207-0bd1685b-90ad-47ea-ada3-e466d7e91fac.jpg)

![Screenshot from 2021-07-17 09-58-16](https://user-images.githubusercontent.com/77866740/126026209-6a11afff-5736-40c3-bd0c-7648f962234a.jpg)


1. For the live link you have to configure one more step. You don’t need to configure this for localhost. Form the left side menu, select **Add Product** and select **Facebook** from the options.
Then click **Facebook Login** -> **Settings** from the left side menu and give your application live redirect URI link in **Valid OAuth Redirect URIs**.

![Screenshot from 2021-07-17 11-03-55](https://user-images.githubusercontent.com/77866740/126026475-e1b2a868-d137-4c86-bcb4-aeb21b96e768.jpg)

1. Then click App Mode from upper menu and make it live.

![Screenshot from 2021-07-17 11-03-55(1)](https://user-images.githubusercontent.com/77866740/126026479-8540fbf2-d544-40c3-a163-a18a1e2978c4.jpg)





