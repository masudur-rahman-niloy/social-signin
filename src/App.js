import logo from './logo.svg';
import './App.css';
import { useEffect, useState } from 'react';
import { loadGoogleScript } from './lib/google_sdk';
import { loadFacebookScript } from './lib/fb_sdk';

const googleClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;

function App() {
  //const location = useLocation();
  const [provider, setProvider] = useState();  
  const [gapi, setGapi] = useState();  
  const [googleAuth, setGoogleAuth] = useState();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [imageUrl, setImageUrl] = useState();
  
  
  // For google part
  const onSuccess = (googleUser) => {
    //console.log('for getting token session we have to call this ', googleUser.getAuthResponse())
    //we also can use this function for token session -> googleUser.reloadAuthResponse()
    setIsLoggedIn(true);
    const profile = googleUser.getBasicProfile();
    setName(profile.getName());
    setEmail(profile.getEmail());
    setImageUrl(profile.getImageUrl());
  };
  
  const onFailure = () => {
    setIsLoggedIn(false);
  }

 const logOut = () => {
   
   if(provider === 'google'){
      (async() => {
        await googleAuth.signOut();      
        renderSigninButton(gapi);
      })();

   }   
   else{     
      window.FB.api('/me/permissions', 'delete', null, () => window.FB.logout());   
      window.location.reload()
   }  
   
   setIsLoggedIn(false);
  };
  
  const renderSigninButton = (_gapi) => {
    //provider = "google";
    setProvider("google");
    _gapi.signin2.render('google-signin', {
      'scope': 'profile email',
      'width': 240,
      'height': 50,
      'longtitle': true,
      'theme': 'dark',
      'onsuccess': onSuccess,
      'onfailure': onFailure 
    });
  }
  
  // For facebook part
  async function fbLogin() {    
    window.FB.login(checkLoginStatus,{scope: 'email'}); 
  }
  
  function checkLoginStatus(response) {
    if (response.status === 'connected') {
        setProvider("facebook");
        //provider = ;        
        window.FB.api('/me', 'GET', { fields: 'email,name' }, function (response) {
          setIsLoggedIn(true);          
          setName(response.name);
          setEmail(response.email);
          setImageUrl("");   
        });
    }
  }

  useEffect(() => {   
    //Facebook sdk implementation  
    loadFacebookScript().then(); 

    //Google sdk implementation
    
    window.onGoogleScriptLoad = () => {    
      const _gapi = window.gapi;
      setGapi(_gapi);   
      _gapi.load('auth2', () => {
        (async () => { 
          const _googleAuth = await _gapi.auth2.init({
           client_id: googleClientId
          });
          setGoogleAuth(_googleAuth);
          renderSigninButton(_gapi);
        })();
      });
    }
    
    //ensure everything is set before loading the script
    loadGoogleScript();  
});
  
  
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        {!isLoggedIn &&
          <button id="google-signin">Login with Google</button>
          
        }
        {!isLoggedIn &&
          <button id="facebook-signin" onClick={fbLogin}>Login with Facebook</button>          
        }
        
        {isLoggedIn &&
          <div>
            <div>
              <input type="image" img src={imageUrl} alt="description of image"/>
            </div>
            <div>{name}</div>
            <div>{email}</div>
            <button className='btn-primary' onClick={logOut}>Log Out</button>
          </div>
        }
      </header>
    </div>
  );
}

export default App;
