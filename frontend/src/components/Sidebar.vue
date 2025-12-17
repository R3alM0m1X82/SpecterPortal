<template>
  <div 
    class="w-64 shadow-lg flex flex-col transition-colors duration-300"
    :class="isDark ? 'bg-gray-800' : 'bg-white'"
  >
    <!-- Header -->
    <div class="p-6 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
      <div class="flex items-center space-x-3">
        <h1 class="text-2xl font-bold">
          <span class="logo-specter">Specter</span><span :class="isDark ? 'text-white' : 'text-gray-800'">Portal</span>
        </h1>
      </div>
    </div>
    
    <!-- Navigation -->
    <nav class="flex-1 p-4 space-y-2 overflow-y-auto">
      <router-link 
        to="/" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Azure Monitor Dashboard Icon - OFFICIAL Microsoft -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="dashboard-grad" x1="8.141" y1="1.048" x2="8.141" y2="13.741" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#5ea0ef"/><stop offset="1" stop-color="#0078d4"/></linearGradient></defs><rect y="0.609" width="16.282" height="13.678" rx="0.761" fill="url(#dashboard-grad)"/><ellipse cx="6.524" cy="5.329" rx="1.131" ry="1.137" fill="#fff"/><ellipse cx="9.659" cy="7.46" rx="1.131" ry="1.137" fill="#fff"/><ellipse cx="12.695" cy="3.422" rx="1.131" ry="1.137" fill="#fff"/><ellipse cx="3.587" cy="9.511" rx="1.131" ry="1.137" fill="#fff"/><polygon points="3.996 9.798 3.177 9.224 6.398 4.64 9.546 6.778 12.296 3.122 13.095 3.723 9.773 8.141 6.65 6.02 3.996 9.798" fill="#fff"/><path d="M6.931,17.092a1.169,1.169,0,0,1-1.168-1.167c.2-3.889,2.539-6.362,5.974-6.362s5.79,2.473,5.974,6.3A1.17,1.17,0,0,1,16.6,17.09l-9.67,0Z" fill="#fff"/><path d="M11.737,9.85c3.427,0,5.52,2.549,5.687,6.029a.881.881,0,0,1-.836.924H6.931a.88.88,0,0,1-.881-.88c0-.015,0-.03,0-.046C6.227,12.4,8.316,9.85,11.737,9.85m0-.575c-3.6,0-6.058,2.581-6.26,6.574v.076a1.458,1.458,0,0,0,1.456,1.454h9.626l.059,0A1.457,1.457,0,0,0,18,15.85c-.189-3.932-2.705-6.575-6.261-6.575Z" fill="#0078d4"/><path d="M14.368,12.272a3.991,3.991,0,0,0-2.382-1.014v1.851a2.224,2.224,0,0,1,1.106.472Z" fill="#50e6ff"/><path d="M9.044,12.272l1.276,1.309a2.224,2.224,0,0,1,1.106-.472V11.258A3.994,3.994,0,0,0,9.044,12.272Z" fill="#50e6ff"/><path d="M13.5,13.993a2.35,2.35,0,0,1,.462,1.136h1.8a4.231,4.231,0,0,0-.987-2.445Z" fill="#32bedd"/><path d="M9.917,13.993,8.641,12.684a4.223,4.223,0,0,0-.986,2.445h1.8A2.352,2.352,0,0,1,9.917,13.993Z" fill="#50e6ff"/><path d="M14.773,13.526a.4.4,0,0,0-.363-.233.388.388,0,0,0-.167.038l-2.772,1.3.334.726,2.775-1.3A.4.4,0,0,0,14.773,13.526Z" fill="#e62323"/><circle cx="11.737" cy="14.963" r="0.954" fill="#4f4f4f"/></svg>
        Dashboard
      </router-link>
      
      <router-link 
        to="/tokens" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- JSON Web Token Icon - OFFICIAL -->
        <svg class="icon mr-3" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><polygon fill="#546e7a" points="21.906,31.772 24.507,29.048 27.107,31.772 27.107,43 21.906,43"/><polygon fill="#f50057" points="17.737,29.058 21.442,28.383 21.945,32.115 15.345,41.199 11.138,38.141"/><polygon fill="#d500f9" points="15.962,24.409 19.355,26.041 17.569,29.356 6.89,32.825 5.283,27.879"/><polygon fill="#29b6f6" points="17.256,19.607 19.042,22.922 15.649,24.554 4.97,21.084 6.577,16.137"/><polygon fill="#00e5ff" points="21.126,16.482 20.623,20.214 16.918,19.539 10.318,10.455 14.526,7.398"/><polygon fill="#546e7a" points="26.094,16.228 23.493,18.952 20.893,16.228 20.893,5 26.094,5"/><polygon fill="#f50057" points="30.262,18.943 26.558,19.618 26.055,15.886 32.654,6.802 36.862,9.859"/><polygon fill="#d500f9" points="32.039,23.59 28.645,21.958 30.431,18.643 41.11,15.174 42.717,20.12"/><polygon fill="#29b6f6" points="30.744,28.393 28.958,25.078 32.351,23.447 43.03,26.916 41.423,31.863"/><polygon fill="#00e5ff" points="26.874,31.518 27.378,27.786 31.082,28.461 37.682,37.545 33.474,40.602"/></svg>
        Tokens
      </router-link>
      
      <router-link 
        to="/search" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Cognitive Search Icon - OFFICIAL Microsoft Azure -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="search-grad" x1="9" y1="0.36" x2="9" y2="18.31" gradientUnits="userSpaceOnUse"><stop offset="0.18" stop-color="#5ea0ef"/><stop offset="1" stop-color="#0078d4"/></linearGradient></defs><path d="M18,11.32a4.12,4.12,0,0,0-3.51-4,5.15,5.15,0,0,0-5.25-5,5.25,5.25,0,0,0-5,3.49A4.86,4.86,0,0,0,0,10.59a5,5,0,0,0,5.07,4.82l.44,0h8.21a.78.78,0,0,0,.22,0A4.13,4.13,0,0,0,18,11.32Z" fill="url(#search-grad)"/><path d="M12.33,6.59a3.07,3.07,0,0,0-5.61.85,3.16,3.16,0,0,0,.33,2.27L4.71,12.08a.79.79,0,0,0,0,1.12.78.78,0,0,0,.56.23.76.76,0,0,0,.56-.23l2.33-2.36a3.14,3.14,0,0,0,.81.33,3.08,3.08,0,0,0,3.36-4.58Zm-.54,2.1A2.16,2.16,0,0,1,9.7,10.34a1.79,1.79,0,0,1-.51-.07,1.87,1.87,0,0,1-.7-.32,2.13,2.13,0,0,1-.56-.56,2.17,2.17,0,0,1-.31-1.73A2.14,2.14,0,0,1,9.7,6a2.31,2.31,0,0,1,.52.06,2.18,2.18,0,0,1,1.32,1A2.13,2.13,0,0,1,11.79,8.69Z" fill="#f2f2f2"/><ellipse cx="9.69" cy="8.18" rx="2.15" ry="2.16" fill="#83b9f9"/></svg>
        Search & Discovery
      </router-link>
      
      <router-link 
        to="/advanced-queries" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- API Center Icon - OFFICIAL Microsoft Azure -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="api-grad1" x1="9" y1="18" x2="9" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#198ab3"/><stop offset="1" stop-color="#32bedd"/></linearGradient><linearGradient id="api-grad2" x1="7.203" y1="11.089" x2="7.203" y2="3.888" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#6f4bb2"/><stop offset="1" stop-color="#c69aeb"/></linearGradient></defs><path d="m11.844,12.791c-.316-.081-.641-.073-.947.015l-1.295-2.124c-.04-.065-.124-.087-.19-.049l-.536.309c-.068.039-.091.128-.05.195l1.296,2.127c-.667.668-.737,1.797.01,2.551.12.121.259.223.41.302.276.143.568.213.857.213.463,0,.916-.18,1.273-.527.125-.121.23-.263.31-.417.302-.579.28-1.233-.037-1.769-.245-.413-.636-.707-1.102-.826Zm.424,1.965c-.06.232-.207.428-.414.55-.207.122-.449.156-.682.097-.278-.071-.503-.267-.614-.541-.141-.349-.041-.762.245-1.007.171-.147.379-.222.592-.222.075,0,.151.009.225.029.233.06.428.206.551.413h0c.122.207.157.448.097.681Zm3.555-9.443c-1.012,0-1.863.695-2.106,1.631h-2.54c-.078,0-.141.063-.141.141v.806c0,.078.063.141.141.141h2.54c.243.937,1.093,1.631,2.106,1.631,1.201,0,2.177-.976,2.177-2.175s-.977-2.175-2.177-2.175Zm1.068,2.388c-.082.428-.427.772-.854.854-.766.146-1.428-.515-1.282-1.28.082-.428.426-.772.854-.854.766-.147,1.429.515,1.283,1.28ZM2.978,2.953c.121.03.244.045.366.045.144,0,.286-.022.423-.063l.884,1.447c.04.065.124.087.19.049l.406-.234c.068-.039.091-.128.05-.195l-.887-1.453c.468-.475.577-1.224.218-1.821-.206-.343-.534-.585-.923-.682-.445-.111-.909-.016-1.28.267-.547.417-.737,1.18-.45,1.805.195.424.559.725,1.004.835Zm-.083-2.056c.133-.097.288-.148.445-.148.061,0,.122.008.183.023.232.058.42.219.514.446.13.315.02.691-.258.889-.182.13-.405.172-.619.118-.232-.058-.42-.219-.514-.446-.129-.312-.023-.683.249-.883Zm2.717,10.093l-.828-.477c-.067-.039-.154-.016-.192.052l-1.473,2.577c-1.227-.327-2.587.325-3.009,1.668-.091.289-.125.595-.1.897.071.849.537,1.569,1.253,1.973.377.212.793.321,1.214.321.374,0,.752-.086,1.109-.259.289-.14.549-.34.758-.583.56-.652.743-1.497.522-2.293-.12-.432-.352-.813-.668-1.116l1.468-2.567c.038-.067.015-.153-.052-.192Zm-2.055,5.145l-.213.234c-.161.177-.367.315-.601.366-.298.065-.605.02-.873-.131-.288-.162-.495-.427-.584-.745-.089-.318-.048-.652.115-.939.227-.402.648-.628,1.08-.628.206,0,.415.051.606.16.288.162.495.427.584.745.089.318.048.652-.115.939Z" fill="url(#api-grad1)"/><path d="m9.921,5.287l-2.172-1.253c-.339-.195-.757-.195-1.096,0l-2.172,1.253c-.339.196-.548.557-.548.948v2.505c0,.391.209.753.548.949l2.174,1.253c.339.195.757.195,1.096,0l2.174-1.253c.339-.196.548-.557.548-.949v-2.505c-.001-.392-.212-.754-.552-.948Z" fill="url(#api-grad2)"/></svg>
        Advanced Queries
      </router-link>
      
      <div :class="isDark ? 'border-t border-gray-700 my-4' : 'border-t border-gray-200 my-4'"></div>
      
      <!-- MS 365 Section -->
      <div class="px-4 py-2">
        <h3 class="text-xs font-bold uppercase tracking-wider" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
          MS 365
        </h3>
      </div>
      
      <router-link 
        to="/emails" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Outlook Icon - OFFICIAL Microsoft -->
        <svg class="icon mr-3" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="outlook-grad1" x1="10" y1="16" x2="30" y2="16" gradientUnits="userSpaceOnUse"><stop stop-color="#064484"/><stop offset="1" stop-color="#0F65B5"/></linearGradient><linearGradient id="outlook-grad2" x1="8" y1="26.7692" x2="32" y2="26.7692" gradientUnits="userSpaceOnUse"><stop stop-color="#1B366F"/><stop offset="1" stop-color="#2657B0"/></linearGradient><linearGradient id="outlook-grad3" x1="32" y1="23" x2="8" y2="23" gradientUnits="userSpaceOnUse"><stop stop-color="#44DCFD"/><stop offset="0.453125" stop-color="#259ED0"/></linearGradient><linearGradient id="outlook-grad4" x1="8" y1="23" x2="32" y2="23" gradientUnits="userSpaceOnUse"><stop stop-color="#259ED0"/><stop offset="1" stop-color="#44DCFD"/></linearGradient><linearGradient id="outlook-grad5" x1="0" y1="16" x2="18" y2="16" gradientUnits="userSpaceOnUse"><stop stop-color="#064484"/><stop offset="1" stop-color="#0F65B5"/></linearGradient></defs><rect x="10" y="2" width="20" height="28" rx="2" fill="#1066B5"/><rect x="10" y="2" width="20" height="28" rx="2" fill="url(#outlook-grad1)"/><rect x="10" y="5" width="10" height="10" fill="#32A9E7"/><rect x="10" y="15" width="10" height="10" fill="#167EB4"/><rect x="20" y="15" width="10" height="10" fill="#32A9E7"/><rect x="20" y="5" width="10" height="10" fill="#58D9FD"/><mask id="outlook-mask" style="mask-type:alpha" maskUnits="userSpaceOnUse" x="8" y="14" width="24" height="16"><path d="M8 14H30C31.1046 14 32 14.8954 32 16V28C32 29.1046 31.1046 30 30 30H10C8.89543 30 8 29.1046 8 28V14Z" fill="url(#outlook-grad2)"/></mask><g mask="url(#outlook-mask)"><path d="M32 14V18H30V14H32Z" fill="#135298"/><path d="M32 30V16L7 30H32Z" fill="url(#outlook-grad3)"/><path d="M8 30V16L33 30H8Z" fill="url(#outlook-grad4)"/></g><path d="M8 12C8 10.3431 9.34315 9 11 9H17C18.6569 9 20 10.3431 20 12V24C20 25.6569 18.6569 27 17 27H8V12Z" fill="#000000" fill-opacity="0.3"/><rect y="7" width="18" height="18" rx="2" fill="url(#outlook-grad5)"/><path d="M14 16.0693V15.903C14 13.0222 11.9272 11 9.01582 11C6.08861 11 4 13.036 4 15.9307V16.097C4 18.9778 6.07278 21 9 21C11.9114 21 14 18.964 14 16.0693ZM11.6424 16.097C11.6424 18.0083 10.5665 19.1579 9.01582 19.1579C7.46519 19.1579 6.37342 17.9806 6.37342 16.0693V15.903C6.37342 13.9917 7.44937 12.8421 9 12.8421C10.5348 12.8421 11.6424 14.0194 11.6424 15.9307V16.097Z" fill="white"/></svg>
        Emails
      </router-link>
      
      <router-link 
        to="/files" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- OneDrive Icon - OFFICIAL Microsoft -->
        <svg class="icon mr-3" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="onedrive-grad1" x1="4.42591" y1="24.6668" x2="27.2309" y2="23.2764" gradientUnits="userSpaceOnUse"><stop stop-color="#2086B8"/><stop offset="1" stop-color="#46D3F6"/></linearGradient><linearGradient id="onedrive-grad2" x1="23.8302" y1="19.6668" x2="30.2108" y2="15.2082" gradientUnits="userSpaceOnUse"><stop stop-color="#1694DB"/><stop offset="1" stop-color="#62C3FE"/></linearGradient><linearGradient id="onedrive-grad3" x1="8.51037" y1="7.33333" x2="23.3335" y2="15.9348" gradientUnits="userSpaceOnUse"><stop stop-color="#0D3D78"/><stop offset="1" stop-color="#063B83"/></linearGradient><linearGradient id="onedrive-grad4" x1="-0.340429" y1="19.9998" x2="14.5634" y2="14.4649" gradientUnits="userSpaceOnUse"><stop stop-color="#16589B"/><stop offset="1" stop-color="#1464B7"/></linearGradient></defs><mask id="onedrive-mask" style="mask-type:alpha" maskUnits="userSpaceOnUse" x="0" y="6" width="32" height="20"><path d="M7.82979 26C3.50549 26 0 22.5675 0 18.3333C0 14.1921 3.35322 10.8179 7.54613 10.6716C9.27535 7.87166 12.4144 6 16 6C20.6308 6 24.5169 9.12183 25.5829 13.3335C29.1316 13.3603 32 16.1855 32 19.6667C32 23.0527 29 26 25.8723 25.9914L7.82979 26Z" fill="#C4C4C4"/></mask><g mask="url(#onedrive-mask)"><path d="M7.83017 26.0001C5.37824 26.0001 3.18957 24.8966 1.75391 23.1691L18.0429 16.3335L30.7089 23.4647C29.5926 24.9211 27.9066 26.0001 26.0004 25.9915C23.1254 26.0001 12.0629 26.0001 7.83017 26.0001Z" fill="url(#onedrive-grad1)"/><path d="M25.5785 13.3149L18.043 16.3334L30.709 23.4647C31.5199 22.4065 32.0004 21.0916 32.0004 19.6669C32.0004 16.1857 29.1321 13.3605 25.5833 13.3337C25.5817 13.3274 25.5801 13.3212 25.5785 13.3149Z" fill="url(#onedrive-grad2)"/><path d="M7.06445 10.7028L18.0423 16.3333L25.5779 13.3148C24.5051 9.11261 20.6237 6 15.9997 6C12.4141 6 9.27508 7.87166 7.54586 10.6716C7.3841 10.6773 7.22358 10.6877 7.06445 10.7028Z" fill="url(#onedrive-grad3)"/><path d="M1.7535 23.1687L18.0425 16.3331L7.06471 10.7026C3.09947 11.0792 0 14.3517 0 18.3331C0 20.1665 0.657197 21.8495 1.7535 23.1687Z" fill="url(#onedrive-grad4)"/></g></svg>
        OneDrive
      </router-link>
      
      <router-link 
        to="/sharepoint" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- SharePoint Icon - OFFICIAL Microsoft -->
        <svg class="icon mr-3" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="sharepoint-grad1" x1="6" y1="11.5" x2="26.5833" y2="11.5" gradientUnits="userSpaceOnUse"><stop stop-color="#103A3B"/><stop offset="1" stop-color="#116B6E"/></linearGradient><linearGradient id="sharepoint-grad2" x1="18" y1="13" x2="32" y2="21" gradientUnits="userSpaceOnUse"><stop stop-color="#1D9097"/><stop offset="1" stop-color="#29BBC2"/></linearGradient><linearGradient id="sharepoint-grad3" x1="12" y1="21.5" x2="23" y2="26.5" gradientUnits="userSpaceOnUse"><stop stop-color="#28A6B5"/><stop offset="1" stop-color="#31D6EC"/></linearGradient><linearGradient id="sharepoint-grad4" x1="0" y1="16" x2="19.5" y2="16" gradientUnits="userSpaceOnUse"><stop stop-color="#105557"/><stop offset="1" stop-color="#116B6E"/></linearGradient></defs><circle cx="15.5" cy="11.5" r="9.5" fill="url(#sharepoint-grad1)"/><circle cx="24" cy="17" r="8" fill="url(#sharepoint-grad2)"/><mask id="sharepoint-mask" style="mask-type:alpha" maskUnits="userSpaceOnUse" x="10" y="6" width="13" height="24"><path d="M23 23.5C23 27.0899 20.0899 30 16.5 30C12.9101 30 10 27.0899 10 23.5C10 19.9102 10 6 10 6H23C23 6 23 21.1988 23 23.5Z" fill="#C4C4C4"/></mask><g mask="url(#sharepoint-mask)"><circle cx="16.5" cy="23.5" r="6.5" fill="url(#sharepoint-grad3)"/><path d="M7 12C7 10.3431 8.34315 9 10 9H17C18.6569 9 20 10.3431 20 12V24C20 25.6569 18.6569 27 17 27H7V12Z" fill="#000000" fill-opacity="0.3"/></g><rect y="7" width="18" height="18" rx="2" fill="url(#sharepoint-grad4)"/><path d="M13 18.1229C13 16.5726 11.9602 15.8883 9.79665 15.0922C8.10273 14.4637 7.70021 14.2821 7.70021 13.6816C7.70021 13.1648 8.20335 12.8156 9.0587 12.8156C9.93082 12.8156 10.7526 13.1089 11.6751 13.6117L12.6143 11.9497C11.6247 11.3352 10.4507 11 9.02516 11C6.84486 11 5.28512 12.1173 5.28512 13.8212C5.28512 15.567 6.52621 16.1257 8.60587 16.8659C10.2662 17.4525 10.5849 17.7458 10.5849 18.2626C10.5849 18.8771 9.9979 19.1844 9.07547 19.1844C7.98532 19.1844 7.02935 18.8073 6.07338 18.1927L5 19.7849C6.174 20.595 7.63312 21 9.12579 21C11.3732 21 13 19.9385 13 18.1229Z" fill="white"/></svg>
        SharePoint
      </router-link>
      
      <router-link 
        to="/teams" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Teams Icon - OFFICIAL Microsoft -->
        <svg class="icon mr-3" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="teams-grad" x1="2.244" x2="6.906" y1="4.46" y2="12.548" gradientUnits="userSpaceOnUse"><stop stop-color="#5A62C3"/><stop offset=".5" stop-color="#4D55BD"/><stop offset="1" stop-color="#3940AB"/></linearGradient></defs><path fill="#5059C9" d="M10.765 6.875h3.616c.342 0 .619.276.619.617v3.288a2.272 2.272 0 01-2.274 2.27h-.01a2.272 2.272 0 01-2.274-2.27V7.199c0-.179.145-.323.323-.323zM13.21 6.225c.808 0 1.464-.655 1.464-1.462 0-.808-.656-1.463-1.465-1.463s-1.465.655-1.465 1.463c0 .807.656 1.462 1.465 1.462z"/><path fill="#7B83EB" d="M8.651 6.225a2.114 2.114 0 002.117-2.112A2.114 2.114 0 008.65 2a2.114 2.114 0 00-2.116 2.112c0 1.167.947 2.113 2.116 2.113zM11.473 6.875h-5.97a.611.611 0 00-.596.625v3.75A3.669 3.669 0 008.488 15a3.669 3.669 0 003.582-3.75V7.5a.611.611 0 00-.597-.625z"/><path fill="#000000" d="M8.814 6.875v5.255a.598.598 0 01-.596.595H5.193a3.951 3.951 0 01-.287-1.476V7.5a.61.61 0 01.597-.624h3.31z" opacity=".1"/><path fill="#000000" d="M8.488 6.875v5.58a.6.6 0 01-.596.595H5.347a3.22 3.22 0 01-.267-.65 3.951 3.951 0 01-.172-1.15V7.498a.61.61 0 01.596-.624h2.985z" opacity=".2"/><path fill="#000000" d="M8.488 6.875v4.93a.6.6 0 01-.596.595H5.08a3.951 3.951 0 01-.172-1.15V7.498a.61.61 0 01.596-.624h2.985z" opacity=".2"/><path fill="#000000" d="M8.163 6.875v4.93a.6.6 0 01-.596.595H5.079a3.951 3.951 0 01-.172-1.15V7.498a.61.61 0 01.596-.624h2.66z" opacity=".2"/><path fill="#000000" d="M8.814 5.195v1.024c-.055.003-.107.006-.163.006-.055 0-.107-.003-.163-.006A2.115 2.115 0 016.593 4.6h1.625a.598.598 0 01.596.594z" opacity=".1"/><path fill="#000000" d="M8.488 5.52v.699a2.115 2.115 0 01-1.79-1.293h1.195a.598.598 0 01.595.594z" opacity=".2"/><path fill="#000000" d="M8.488 5.52v.699a2.115 2.115 0 01-1.79-1.293h1.195a.598.598 0 01.595.594z" opacity=".2"/><path fill="#000000" d="M8.163 5.52v.647a2.115 2.115 0 01-1.465-1.242h.87a.598.598 0 01.595.595z" opacity=".2"/><path fill="url(#teams-grad)" d="M1.597 4.925h5.969c.33 0 .597.267.597.596v5.958a.596.596 0 01-.597.596h-5.97A.596.596 0 011 11.479V5.521c0-.33.267-.596.597-.596z"/><path fill="#ffffff" d="M6.152 7.193H4.959v3.243h-.76V7.193H3.01v-.63h3.141v.63z"/></svg>
        Teams
      </router-link>
      
      <div :class="isDark ? 'border-t border-gray-700 my-4' : 'border-t border-gray-200 my-4'"></div>
      
      <!-- ENTRA ID Section -->
      <div class="px-4 py-2">
        <h3 class="text-xs font-bold uppercase tracking-wider" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
          Entra ID
        </h3>
      </div>
      
      <router-link 
        to="/users-groups" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Groups Icon - OFFICIAL Microsoft Entra ID -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="groups-grad1" x1="6.7" y1="7.26" x2="6.7" y2="18.36" gradientUnits="userSpaceOnUse"><stop offset="0.22" stop-color="#32d4f5"/><stop offset="1" stop-color="#198ab3"/></linearGradient><linearGradient id="groups-grad2" x1="6.42" y1="1.32" x2="7.23" y2="11.39" gradientUnits="userSpaceOnUse"><stop offset="0.22" stop-color="#32d4f5"/><stop offset="1" stop-color="#198ab3"/></linearGradient></defs><path d="M17.22,13.92a.79.79,0,0,0,.8-.79A.28.28,0,0,0,18,13c-.31-2.5-1.74-4.54-4.46-4.54S9.35,10.22,9.07,13a.81.81,0,0,0,.72.88h7.43Z" fill="#0078d4"/><path d="M13.55,9.09a2.44,2.44,0,0,1-1.36-.4l1.35,3.52,1.33-3.49A2.54,2.54,0,0,1,13.55,9.09Z" fill="#fff" opacity="0.8"/><circle cx="13.55" cy="6.58" r="2.51" fill="#0078d4"/><path d="M12.19,16.36a1.19,1.19,0,0,0,1.19-1.19.66.66,0,0,0,0-.14c-.47-3.74-2.6-6.78-6.66-6.78S.44,10.83,0,15a1.2,1.2,0,0,0,1.07,1.31h11.1Z" fill="url(#groups-grad1)"/><path d="M6.77,9.14a3.72,3.72,0,0,1-2-.6l2,5.25,2-5.21A3.81,3.81,0,0,1,6.77,9.14Z" fill="#fff" opacity="0.8"/><circle cx="6.74" cy="5.39" r="3.75" fill="url(#groups-grad2)"/></svg>
        Users & Groups
      </router-link>
      
      <!-- External Users -->
      <router-link 
        to="/external-users" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- External Users / Guest Users Icon -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="ext-grad1" x1="5.5" y1="7.26" x2="5.5" y2="16" gradientUnits="userSpaceOnUse"><stop offset="0.22" stop-color="#ffb900"/><stop offset="1" stop-color="#ff8c00"/></linearGradient><linearGradient id="ext-grad2" x1="5.5" y1="1" x2="5.5" y2="8" gradientUnits="userSpaceOnUse"><stop offset="0.22" stop-color="#ffb900"/><stop offset="1" stop-color="#ff8c00"/></linearGradient></defs><path d="M10.5,15a1,1,0,0,0,1-1,.5.5,0,0,0,0-.1c-.4-3.2-2.2-5.8-5.7-5.8S.4,10.5,0,13.9a1,1,0,0,0,.9,1.1H10.5Z" fill="url(#ext-grad1)"/><circle cx="5.8" cy="4.6" r="3.2" fill="url(#ext-grad2)"/><circle cx="14" cy="5" r="2.5" fill="#0078d4"/><path d="M17.5,10h-4v1.5h4V10z" fill="#0078d4"/><path d="M15.5,8v4" stroke="#0078d4" stroke-width="1.5" fill="none"/></svg>
        External Users
      </router-link>
      
      <router-link 
        to="/applications" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Enterprise Applications Icon - OFFICIAL Microsoft Entra ID -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="apps-grad1" x1="-6784.85" y1="1118.78" x2="-6784.85" y2="1089.98" gradientTransform="matrix(0.5, 0, 0, -0.5, 3400.41, 559.99)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#5ea0ef"/><stop offset="0.18" stop-color="#589eed"/><stop offset="0.41" stop-color="#4897e9"/><stop offset="0.66" stop-color="#2e8ce1"/><stop offset="0.94" stop-color="#0a7cd7"/><stop offset="1" stop-color="#0078d4"/></linearGradient><linearGradient id="apps-grad2" x1="-1.47" y1="14.91" x2="17.16" y2="14.8" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#449cdd" stop-opacity="0.15"/><stop offset="0.16" stop-color="#2870ab" stop-opacity="0"/><stop offset="0.18" stop-color="#2469a3" stop-opacity="0.06"/><stop offset="0.23" stop-color="#1a5991" stop-opacity="0.19"/><stop offset="0.28" stop-color="#144f86" stop-opacity="0.27"/><stop offset="0.34" stop-color="#124c82" stop-opacity="0.3"/><stop offset="0.76" stop-color="#002851" stop-opacity="0.35"/><stop offset="0.9" stop-color="#2f7ab6" stop-opacity="0"/><stop offset="1" stop-color="#449cdd" stop-opacity="0"/></linearGradient><clipPath id="apps-clip"><circle cx="13.26" cy="13.27" r="4.16" fill="none"/></clipPath></defs><path d="M5.61,10.65H9.94V15H5.61Zm-5-5.76H4.89V.57H1.17a.6.6,0,0,0-.6.6ZM1.17,15H4.89V10.65H.57v3.72A.6.6,0,0,0,1.17,15Zm-.6-5H4.89V5.61H.57Zm10.09,5h3.72a.6.6,0,0,0,.6-.6V10.65H10.66Zm-5-5H9.94V5.61H5.61Zm5.05,0H15V5.61H10.66Zm0-9.36V4.89H15V1.17a.6.6,0,0,0-.6-.6Zm-5,4.32H9.94V.57H5.61Z" fill="url(#apps-grad1)"/><path d="M10.66,15h4.15a.59.59,0,0,1-.18-.29h-4Z" opacity="0.95" fill="url(#apps-grad2)"/><circle cx="13.26" cy="13.27" r="4.16" fill="#32bedd"/><g clip-path="url(#apps-clip)"><path d="M17.06,13.87c-.21.11-.51.05-.65.16a1.6,1.6,0,0,0-.63.66c0,.06,0,.15-.07.18-.28.19-.56.39-.3.81-.3,0-.2-.27-.34-.35a.77.77,0,0,0-1.06.54.34.34,0,0,0,.16.37.26.26,0,0,0,.36-.12.18.18,0,0,1,.26-.06c0,.16-.28.45.18.46.12,0,.09.14.06.23s.06.24.19.3,0,0,0,.05,0,0,0,0c-.37,0-.45-.45-.81-.5a4.28,4.28,0,0,1-.43-.14c-.27-.09-.58-.14-.64-.54a.77.77,0,0,0-.36-.49c-.12-.08-.19-.23-.31-.32a1,1,0,0,0-.22-.36.94.94,0,0,1-.14-.87,2.32,2.32,0,0,0-.1-1.68c-.1-.32-.12-.65-.48-.86s-.3.12-.44.05-.22.13-.26.15c-.29.08-.54.33-.91.29.14-.07.25-.11.35-.17s.29-.14.07-.38-.14-.59.45-.83c-.05-.14-.41-.11-.25-.37s.28-.13.43,0c.1-.19-.12-.43.05-.54a2.86,2.86,0,0,1,.72-.29.25.25,0,0,1,.34.11c.18.28.54.33.72.61.05.09.15,0,.22,0,.41-.14.68.12,1,.33s.27.34.53.31a.49.49,0,0,1,.21,0c.16.07.31.11.43-.06a.3.3,0,0,0,.26-.23c.06-.09.09-.22.24-.16A1.15,1.15,0,0,0,16,11c.13-.1.26-.16.11-.39a.37.37,0,0,1,.25-.56.54.54,0,0,1,.63.23c.19.34.25.73.47,1,.07.09,0,.13,0,.2s-.18,0-.28-.06l.07.43a.66.66,0,0,1-.82-.25c0-.12,0-.17.12-.23s.19-.11.19-.24a.19.19,0,0,0-.1-.2c-.08,0-.13,0-.15.09s-.33.25-.28.53-.19.22-.33.14c-.33-.17-.45.13-.59.29s0,.34.16.46.31.21.37.4a.88.88,0,0,0,.29-.58c0-.18.07-.43.32-.46a.43.43,0,0,1,.44.28c.05.11.13.12.23.13a8.79,8.79,0,0,1,.54,1.52l-.37-.05c0-.29-.25-.16-.39-.22C16.84,13.64,17.07,13.69,17.06,13.87Z" fill="#b4ec36"/><path d="M15.62,10.27c-.13-.12-.27-.23-.06-.4s.2-.29.3,0A.37.37,0,0,1,15.62,10.27Z" fill="#b4ec36"/><path d="M15.93,9.87c.11-.11.25-.1.27,0s-.13.19-.26.23S15.85,10,15.93,9.87Z" fill="#b4ec36"/><path d="M15.16,8.94,14.81,9c0-.25.25-.27.42-.23S15.21,8.89,15.16,8.94Z" fill="#b4ec36"/></g></svg>
        Applications
      </router-link>
      
      <router-link 
        to="/devices" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Devices Icon - OFFICIAL Microsoft Entra ID -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="devices-grad" x1="9" y1="15.83" x2="9" y2="5.79" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#0078d4"/><stop offset="1" stop-color="#5ea0ef"/></linearGradient></defs><rect x="1" y="1" width="16" height="11" rx="1" fill="url(#devices-grad)"/><rect x="3" y="3" width="12" height="7" fill="#fff"/><path d="M6,13h6v1a1,1,0,0,1-1,1H7a1,1,0,0,1-1-1Z" fill="#0078d4"/><rect x="5" y="15" width="8" height="2" rx="0.5" fill="#0078d4"/></svg>
        Devices
      </router-link>
      
      <router-link 
        to="/roles-licenses" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Roles & Administrators Icon - OFFICIAL Microsoft Entra ID -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="e78519cd-36d2-4ee5-987f-be84be24d95e" x1="7.93" y1="17.95" x2="7.93" y2="5.62" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#5e9624"/><stop offset="1" stop-color="#b4ec36"/></linearGradient><linearGradient id="ac3f95ec-6391-4f34-b431-9534d4cdf013" x1="7.95" y1="9.21" x2="7.95" y2="-2.02" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#5e9624"/><stop offset="1" stop-color="#b4ec36"/></linearGradient></defs><path d="M14,16.85a1.3,1.3,0,0,0,1.32-1.31.81.81,0,0,0,0-.16c-.52-4.15-2.88-7.53-7.4-7.53S1,10.71.51,15.39A1.34,1.34,0,0,0,1.7,16.85H14Z" fill="url(#e78519cd-36d2-4ee5-987f-be84be24d95e)"/><path d="M8,8.83a4.16,4.16,0,0,1-2.26-.66L7.92,14l2.22-5.79A4.2,4.2,0,0,1,8,8.83Z" fill="#fff"/><circle cx="7.95" cy="4.67" r="4.17" fill="url(#ac3f95ec-6391-4f34-b431-9534d4cdf013)"/><polygon points="17.49 11.13 17.49 15.37 13.85 17.5 13.85 13.26 17.49 11.13" fill="#32bedd"/><polygon points="17.49 11.13 13.85 13.26 10.21 11.13 13.85 9 17.49 11.13" fill="#9cebff"/><polygon points="13.85 13.26 13.85 17.5 10.21 15.37 10.21 11.13 13.85 13.26" fill="#50e6ff"/><polygon points="10.21 15.37 13.85 13.26 13.85 17.5 10.21 15.37" fill="#9cebff"/><polygon points="17.49 15.37 13.85 13.26 13.85 17.5 17.49 15.37" fill="#50e6ff"/></svg>
        Roles & Licenses
      </router-link>
      
      <router-link 
        to="/admin-units" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Administrative Units Icon - OFFICIAL Microsoft Entra ID -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="au-grad1" x1="9.282" y1="12.079" x2="16.974" y2="7.637" gradientUnits="userSpaceOnUse"><stop offset="0.384" stop-color="#005ba1"/><stop offset="0.829" stop-color="#0078d4"/></linearGradient><linearGradient id="au-grad2" x1="5.573" y1="12.94" x2="14.846" y2="7.422" gradientUnits="userSpaceOnUse"><stop offset="0.392" stop-color="#0078d4"/><stop offset="0.961" stop-color="#5ea0ef"/></linearGradient><linearGradient id="au-grad3" x1="7.118" y1="784.39" x2="7.118" y2="775.34" gradientTransform="matrix(1, 0, 0, -1, 0, 791.516)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#83b9f9"/><stop offset="1" stop-color="#5ea0ef"/></linearGradient><linearGradient id="au-grad4" x1="6.919" y1="788.428" x2="7.502" y2="781.18" gradientTransform="matrix(1, 0, 0, -1, 0, 791.516)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#83b9f9"/><stop offset="0.9" stop-color="#5ea0ef"/></linearGradient></defs><path d="M16.235,12.663a3.93,3.93,0,0,0-2.49-3.53,2.045,2.045,0,1,0-2.295-.017c-1.483.423-2.3,1.712-2.49,3.547a.661.661,0,0,0,.587.717l6.053.032a.644.644,0,0,0,.652-.635v-.008A.226.226,0,0,0,16.235,12.663Z" fill="url(#au-grad1)"/><path d="M14.524,13.255C14.275,11.247,13.3,9.54,11.5,8.966a2.485,2.485,0,1,0-2.789-.021c-1.8.514-2.8,2.081-3.025,4.31a.8.8,0,0,0,.713.872l7.355.039a.781.781,0,0,0,.792-.772v-.01A.284.284,0,0,0,14.524,13.255Z" fill="url(#au-grad2)"/><path d="M11.6,15.029a.97.97,0,0,0,.97-.97.543.543,0,0,0,0-.114c-.383-3.05-2.12-5.528-5.43-5.528s-5.121,2.1-5.479,5.5a.977.977,0,0,0,.872,1.068Z" fill="url(#au-grad3)"/><path d="M7.185,9.142a3.036,3.036,0,0,1-1.631-.489l1.631,4.281,1.63-4.248A3.105,3.105,0,0,1,7.185,9.142Z" fill="#fff" opacity="0.8"/><circle cx="7.16" cy="6.085" r="3.058" fill="url(#au-grad4)"/><rect x="1.715" width="2.086" height="0.604" fill="#0078d4"/><polygon points="17.079 0.604 17.418 0.604 17.418 0.932 18 0.932 18 0 17.079 0 17.079 0.604" fill="#0078d4"/><polygon points="0.964 17.354 0.667 17.354 0.667 17.015 0 17.015 0 18 0.964 18 0.964 17.354" fill="#0078d4"/><polygon points="17.418 17.047 17.418 17.354 17.079 17.354 17.079 18 18 18 18 17.047 17.418 17.047" fill="#0078d4"/><polygon points="0.667 0.911 0.667 0.604 0.964 0.604 0.964 0 0 0 0 0.911 0.667 0.911" fill="#0078d4"/><rect x="4.839" width="2.086" height="0.604" fill="#0078d4"/><rect x="7.952" width="2.086" height="0.604" fill="#0078d4"/><rect x="11.075" width="2.086" height="0.604" fill="#0078d4"/><rect x="14.199" width="2.086" height="0.604" fill="#0078d4"/><rect x="1.736" y="17.354" width="2.086" height="0.604" fill="#0078d4"/><rect x="4.849" y="17.354" width="2.086" height="0.604" fill="#0078d4"/><rect x="7.973" y="17.354" width="2.086" height="0.604" fill="#0078d4"/><rect x="11.096" y="17.354" width="2.086" height="0.604" fill="#0078d4"/><rect x="14.209" y="17.354" width="2.086" height="0.604" fill="#0078d4"/><rect x="17.396" y="1.641" width="0.604" height="2.086" fill="#0078d4"/><rect x="17.396" y="4.754" width="0.604" height="2.086" fill="#0078d4"/><rect x="17.396" y="7.878" width="0.604" height="2.086" fill="#0078d4"/><rect x="17.396" y="10.991" width="0.604" height="2.086" fill="#0078d4"/><rect x="17.396" y="14.114" width="0.604" height="2.086" fill="#0078d4"/><rect y="1.62" width="0.604" height="2.086" fill="#0078d4"/><rect y="4.744" width="0.604" height="2.086" fill="#0078d4"/><rect y="7.856" width="0.604" height="2.086" fill="#0078d4"/><rect y="10.98" width="0.604" height="2.086" fill="#0078d4"/><rect y="14.093" width="0.604" height="2.086" fill="#0078d4"/></svg>
        Admin Units
      </router-link>
      
      <router-link 
        to="/tenant" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Tenant Properties Icon - OFFICIAL Microsoft Entra ID -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="tenant-grad1" x1="11.972" y1="14.787" x2="11.972" y2="2.782" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#32bedd"/><stop offset="0.576" stop-color="#32ceef"/><stop offset="1" stop-color="#32d4f5"/></linearGradient><linearGradient id="tenant-grad2" x1="4.699" y1="15.352" x2="4.699" y2="3.839" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#1988d9"/><stop offset="0.9" stop-color="#54aef0"/></linearGradient><linearGradient id="tenant-grad3" x1="1.31" y1="15.346" x2="1.31" y2="3.839" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#005ba1"/><stop offset="1" stop-color="#0078d4"/></linearGradient></defs><path d="M17.975,9.225V8.269a.3.3,0,0,0-.192-.277h0l-1.335-.438a.3.3,0,0,1-.182-.169L15.983,6.7a.3.3,0,0,1,.006-.238l.6-1.279a.3.3,0,0,0-.059-.335l-.662-.663a.3.3,0,0,0-.342-.055h0l-1.248.635a.294.294,0,0,1-.246.01l-.69-.283a.3.3,0,0,1-.166-.173l-.485-1.338a.3.3,0,0,0-.278-.195h-.956a.3.3,0,0,0-.277.192h0l-.438,1.335a.3.3,0,0,1-.169.181l-.688.283a.3.3,0,0,1-.24-.007l-1.254-.6a.3.3,0,0,0-.336.058l-.662.662a.3.3,0,0,0-.056.342h0l.635,1.247a.3.3,0,0,1,.01.247L7.7,7.414a.3.3,0,0,1-.174.166l-1.36.486a.3.3,0,0,0-.2.279V9.3a.3.3,0,0,0,.193.277h0l1.334.437a.3.3,0,0,1,.182.169l.283.69a.3.3,0,0,1-.006.238l-.6,1.279a.3.3,0,0,0,.059.335l.663.663a.3.3,0,0,0,.341.055h0l1.247-.635a.3.3,0,0,1,.247-.01l.689.283a.289.289,0,0,1,.166.173l.485,1.338a.3.3,0,0,0,.279.2h.955a.3.3,0,0,0,.278-.192h0L13.2,13.26a.294.294,0,0,1,.169-.181l.69-.283a.29.29,0,0,1,.238.006l1.279.6a.3.3,0,0,0,.335-.058l.663-.663a.3.3,0,0,0,.055-.342h0L16,11.09a.294.294,0,0,1-.01-.246l.282-.69a.3.3,0,0,1,.173-.166L17.78,9.5A.3.3,0,0,0,17.975,9.225ZM12.24,11.406a2.635,2.635,0,1,1,2.354-2.353A2.635,2.635,0,0,1,12.24,11.406Z" fill="url(#tenant-grad1)"/><path d="M.049,3.85.954,2.8a.441.441,0,0,1,.332-.151H9.964a.608.608,0,0,1,.664.621V14.041a.24.24,0,0,1-.083.182L9.282,15.316H.636l-.6-.252Z" fill="#005ba1"/><path d="M.777,3.846l.555-.633a.392.392,0,0,1,.294-.133h8.1a.39.39,0,0,1,.39.39v10.3a.391.391,0,0,1-.127.289l-.866.788Z" fill="#fff"/><path d="M9.139,3.839H.1A.058.058,0,0,0,.036,3.9V15.13a.222.222,0,0,0,.222.222H9.139a.223.223,0,0,0,.223-.222V4.061A.222.222,0,0,0,9.139,3.839Z" fill="url(#tenant-grad2)"/><path d="M.071,3.839H2.594a0,0,0,0,1,0,0V15.346a0,0,0,0,1,0,0H.213a.188.188,0,0,1-.188-.188V3.885A.046.046,0,0,1,.071,3.839Z" fill="url(#tenant-grad3)"/></svg>
        Tenant
      </router-link>
      
      <router-link 
        to="/cap" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Conditional Access Icon - OFFICIAL Microsoft Entra ID -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="cap-grad1" x1="9" y1="16.79" x2="9" y2="1.21" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#0078d4"/><stop offset="0.06" stop-color="#0a7cd7"/><stop offset="0.34" stop-color="#2e8ce1"/><stop offset="0.59" stop-color="#4897e9"/><stop offset="0.82" stop-color="#589eed"/><stop offset="1" stop-color="#5ea0ef"/></linearGradient></defs><path d="M16.08,8.44c0,4.57-5.62,8.25-6.85,9a.43.43,0,0,1-.46,0c-1.23-.74-6.85-4.42-6.85-9V2.94a.44.44,0,0,1,.43-.44C6.73,2.39,5.72.5,9,.5s2.27,1.89,6.65,2a.44.44,0,0,1,.43.44Z" fill="#0078d4"/><path d="M15.5,8.48c0,4.2-5.16,7.57-6.29,8.25a.4.4,0,0,1-.42,0C7.66,16.05,2.5,12.68,2.5,8.48v-5A.41.41,0,0,1,2.9,3C6.92,2.93,6,1.21,9,1.21S11.08,2.93,15.1,3a.41.41,0,0,1,.4.4Z" fill="url(#cap-grad1)"/><path d="M11.85,7.66h-.4V6.24a2.62,2.62,0,0,0-.7-1.81,2.37,2.37,0,0,0-3.48,0,2.61,2.61,0,0,0-.7,1.81V7.66h-.4A.32.32,0,0,0,5.82,8v3.68a.32.32,0,0,0,.33.32h5.7a.32.32,0,0,0,.33-.32V8A.32.32,0,0,0,11.85,7.66Zm-1.55,0H7.7V6.22a1.43,1.43,0,0,1,.41-1,1.19,1.19,0,0,1,1.78,0,1.56,1.56,0,0,1,.16.2h0a1.4,1.4,0,0,1,.25.79Z" fill="#ffbd02"/><path d="M6.152,7.66h5.7a.32.32,0,0,1,.21.08L5.94,11.9a.33.33,0,0,1-.12-.24V8A.32.32,0,0,1,6.152,7.66Z" fill="#ffe452"/><path d="M11.85,7.66H6.152a.32.32,0,0,0-.21.08l6.12,4.16a.3.3,0,0,0,.12-.24V8A.32.32,0,0,0,11.85,7.66Z" fill="#ffd400" opacity="0.5"/></svg>
        CA Policies
      </router-link>
      
      <div :class="isDark ? 'border-t border-gray-700 my-4' : 'border-t border-gray-200 my-4'"></div>
      
      <!-- Azure Section -->
      <div class="px-4 py-2">
        <h3 class="text-xs font-bold uppercase tracking-wider" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
          Azure
        </h3>
      </div>
      
      <!-- My Permissions - PRIMO ELEMENTO SEZIONE AZURE -->
      <router-link 
        to="/azure/permissions" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Resource Groups Icon - OFFICIAL Microsoft Azure -->
        <svg class="icon mr-3" id="a685cc8c-32ba-4d54-91da-3a125cb58ded" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 18"><g><g><path d="M.5,15.08a.16.16,0,0,0,.08.14l1.16.65L3.7,17a.17.17,0,0,0,.23-.06l.66-1.12a.16.16,0,0,0-.06-.21l-2.3-1.3a.17.17,0,0,1-.08-.14V3.85a.16.16,0,0,1,.08-.14l2.3-1.3a.16.16,0,0,0,.06-.21L3.93,1.08A.17.17,0,0,0,3.7,1L1.78,2.11l-1.2.67a.16.16,0,0,0-.08.14V15.08Z" fill="#949494"/><path d="M2.14,3.77l.06-.06,2.3-1.3a.14.14,0,0,0,.06-.21L3.9,1.08A.15.15,0,0,0,3.68,1L1.75,2.11.56,2.78s-.05,0-.06.06l.9.51Z" fill="#a3a3a3"/><path d="M4.5,15.59l-2.3-1.3a.22.22,0,0,1-.07-.09l-1.62,1,.05,0,1.15.65,2,1.11a.15.15,0,0,0,.22-.06l.66-1.12A.14.14,0,0,0,4.5,15.59Z" fill="#a3a3a3"/></g><path d="M17.5,15.08a.16.16,0,0,1-.08.14l-1.16.65L14.3,17a.17.17,0,0,1-.23-.06l-.66-1.12a.16.16,0,0,1,.06-.21l2.3-1.3a.17.17,0,0,0,.08-.14V3.85a.16.16,0,0,0-.08-.14l-2.3-1.3a.16.16,0,0,1-.06-.21l.66-1.12A.17.17,0,0,1,14.3,1l1.92,1.09,1.2.67a.16.16,0,0,1,.08.14V15.08Z" fill="#949494"/><path d="M15.86,3.77l-.06-.06-2.3-1.3a.14.14,0,0,1-.06-.21l.66-1.12A.15.15,0,0,1,14.32,1l1.93,1.09,1.19.67s0,0,.06.06l-.9.51Z" fill="#a3a3a3"/><path d="M13.5,15.59l2.3-1.3a.22.22,0,0,0,.07-.09l1.62,1,0,0-1.15.65-2,1.11a.15.15,0,0,1-.22-.06l-.66-1.12A.14.14,0,0,1,13.5,15.59Z" fill="#a3a3a3"/><polygon points="14.31 5.93 14.31 12.07 8.99 15.16 8.99 9.01 14.31 5.93" fill="#32bedd"/><polygon points="14.31 5.93 9 9.02 3.68 5.93 9 2.84 14.31 5.93" fill="#9cebff"/><polygon points="8.99 9.02 8.99 15.16 3.68 12.07 3.68 5.93 8.99 9.02" fill="#50e6ff"/><polygon points="3.68 12.07 8.99 9.01 8.99 15.16 3.68 12.07" fill="#9cebff"/><polygon points="14.31 12.07 8.99 9.01 8.99 15.16 14.31 12.07" fill="#50e6ff"/></g></svg>
        My Permissions
      </router-link>
      
      <router-link 
        to="/azure/virtual-machines" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Virtual Machine Icon - OFFICIAL Microsoft Azure -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="vm-grad1" x1="8.88" y1="12.21" x2="8.88" y2="0.21" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#0078d4"/><stop offset="0.82" stop-color="#5ea0ef"/></linearGradient><linearGradient id="vm-grad2" x1="8.88" y1="16.84" x2="8.88" y2="12.21" gradientUnits="userSpaceOnUse"><stop offset="0.15" stop-color="#ccc"/><stop offset="1" stop-color="#707070"/></linearGradient></defs><rect x="-0.12" y="0.21" width="18" height="12" rx="0.6" fill="url(#vm-grad1)"/><polygon points="11.88 4.46 11.88 7.95 8.88 9.71 8.88 6.21 11.88 4.46" fill="#50e6ff"/><polygon points="11.88 4.46 8.88 6.22 5.88 4.46 8.88 2.71 11.88 4.46" fill="#c3f1ff"/><polygon points="8.88 6.22 8.88 9.71 5.88 7.95 5.88 4.46 8.88 6.22" fill="#9cebff"/><polygon points="5.88 7.95 8.88 6.21 8.88 9.71 5.88 7.95" fill="#c3f1ff"/><polygon points="11.88 7.95 8.88 6.21 8.88 9.71 11.88 7.95" fill="#9cebff"/><path d="M12.49,15.84c-1.78-.28-1.85-1.56-1.85-3.63H7.11c0,2.07-.06,3.35-1.84,3.63a1,1,0,0,0-.89,1h9A1,1,0,0,0,12.49,15.84Z" fill="url(#vm-grad2)"/></svg>
        Virtual Machines
      </router-link>
      
      <router-link 
        to="/azure/storage-accounts" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Storage Accounts Icon - OFFICIAL Microsoft Azure -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="storage-grad" x1="9" y1="15.83" x2="9" y2="5.79" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#b3b3b3"/><stop offset="0.26" stop-color="#c1c1c1"/><stop offset="1" stop-color="#e6e6e6"/></linearGradient></defs><path d="M.5,5.79h17a0,0,0,0,1,0,0v9.48a.57.57,0,0,1-.57.57H1.07a.57.57,0,0,1-.57-.57V5.79A0,0,0,0,1,.5,5.79Z" fill="url(#storage-grad)"/><path d="M1.07,2.17H16.93a.57.57,0,0,1,.57.57V5.79a0,0,0,0,1,0,0H.5a0,0,0,0,1,0,0V2.73A.57.57,0,0,1,1.07,2.17Z" fill="#37c2b1"/><path d="M2.81,6.89H15.18a.27.27,0,0,1,.26.27v1.4a.27.27,0,0,1-.26.27H2.81a.27.27,0,0,1-.26-.27V7.16A.27.27,0,0,1,2.81,6.89Z" fill="#fff"/><path d="M2.82,9.68H15.19a.27.27,0,0,1,.26.27v1.41a.27.27,0,0,1-.26.27H2.82a.27.27,0,0,1-.26-.27V10A.27.27,0,0,1,2.82,9.68Z" fill="#37c2b1"/><path d="M2.82,12.5H15.19a.27.27,0,0,1,.26.27v1.41a.27.27,0,0,1-.26.27H2.82a.27.27,0,0,1-.26-.27V12.77A.27.27,0,0,1,2.82,12.5Z" fill="#258277"/></svg>
        Storage Accounts
      </router-link>
      
      <router-link 
        to="/azure/key-vaults" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Key Vaults Icon - OFFICIAL Microsoft Azure -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><radialGradient id="kv-grad1" cx="9" cy="9" r="8.5" gradientUnits="userSpaceOnUse"><stop offset="0.18" stop-color="#5ea0ef"/><stop offset="0.56" stop-color="#5c9fee"/><stop offset="0.69" stop-color="#559ced"/><stop offset="0.78" stop-color="#4a97e9"/><stop offset="0.86" stop-color="#3990e4"/><stop offset="0.93" stop-color="#2387de"/><stop offset="0.99" stop-color="#087bd6"/><stop offset="1" stop-color="#0078d4"/></radialGradient><radialGradient id="kv-grad2" cx="38.95" cy="182.07" r="9.88" gradientTransform="translate(-28.71 -163.24) scale(0.94 0.94)" gradientUnits="userSpaceOnUse"><stop offset="0.27" stop-color="#ffd70f"/><stop offset="0.49" stop-color="#ffcb12"/><stop offset="0.88" stop-color="#feac19"/><stop offset="1" stop-color="#fea11b"/></radialGradient></defs><path d="M9,.5A8.5,8.5,0,1,0,17.5,9,8.51,8.51,0,0,0,9,.5ZM9,16.34A7.34,7.34,0,1,1,16.34,9,7.34,7.34,0,0,1,9,16.34Z" fill="url(#kv-grad1)"/><circle cx="9" cy="9" r="7.34" fill="#fff"/><path d="M13.44,7.33a1.84,1.84,0,0,0,0-2.59h0L10.29,1.58a1.83,1.83,0,0,0-2.58,0h0L4.56,4.74a1.84,1.84,0,0,0,0,2.59L7.18,10a.51.51,0,0,1,.15.36v4.88a.63.63,0,0,0,.18.44l1.2,1.2a.41.41,0,0,0,.58,0l1.16-1.16h0l.68-.68a.25.25,0,0,0,0-.34l-.49-.49a.27.27,0,0,1,0-.37l.49-.49a.25.25,0,0,0,0-.34l-.49-.49a.27.27,0,0,1,0-.37l.49-.49a.25.25,0,0,0,0-.34l-.68-.69v-.25ZM9,2.35A1,1,0,0,1,9,4.42,1,1,0,1,1,9,2.35Z" fill="url(#kv-grad2)"/><path d="M8.18,15.3h0a.23.23,0,0,0,.38-.17v-4a.24.24,0,0,0-.11-.2h0a.22.22,0,0,0-.34.2v4A.28.28,0,0,0,8.18,15.3Z" fill="#ff9300" opacity="0.75"/><rect x="6.48" y="5.79" width="5.17" height="0.61" rx="0.28" fill="#ff9300" opacity="0.75"/><rect x="6.48" y="6.78" width="5.17" height="0.61" rx="0.28" fill="#ff9300" opacity="0.75"/></svg>
        Key Vaults
      </router-link>
      
      <router-link 
        to="/azure/sql-databases" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Azure SQL Icon - Official az-icons.com -->
        <svg class="icon mr-3" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="sql-grad1" x1="2.59" y1="10.16" x2="15.41" y2="10.16" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#005ba1"/><stop offset="0.07" stop-color="#0060a9"/><stop offset="0.36" stop-color="#0071c8"/><stop offset="0.52" stop-color="#0078d4"/><stop offset="0.64" stop-color="#0074cd"/><stop offset="0.82" stop-color="#006abb"/><stop offset="1" stop-color="#005ba1"/></linearGradient><radialGradient id="sql-grad2" cx="9.36" cy="10.57" r="7.07" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#f2f2f2"/><stop offset="0.58" stop-color="#eee"/><stop offset="1" stop-color="#e6e6e6"/></radialGradient></defs><path d="M9,5.14c-3.54,0-6.41-1-6.41-2.32V15.18c0,1.27,2.82,2.3,6.32,2.32H9c3.54,0,6.41-1,6.41-2.32V2.82C15.41,4.11,12.54,5.14,9,5.14Z" fill="url(#sql-grad1)"/><path d="M15.41,2.82c0,1.29-2.87,2.32-6.41,2.32s-6.41-1-6.41-2.32S5.46.5,9,.5s6.41,1,6.41,2.32" fill="#e8e8e8"/><path d="M13.92,2.63c0,.82-2.21,1.48-4.92,1.48S4.08,3.45,4.08,2.63,6.29,1.16,9,1.16s4.92.66,4.92,1.47" fill="#50e6ff"/><path d="M9,3a11.55,11.55,0,0,0-3.89.57A11.42,11.42,0,0,0,9,4.11a11.15,11.15,0,0,0,3.89-.58A11.84,11.84,0,0,0,9,3Z" fill="#198ab3"/><path d="M12.9,11.4V8H12v4.13h2.46V11.4ZM5.76,9.73a1.83,1.83,0,0,1-.51-.31.44.44,0,0,1-.12-.32.34.34,0,0,1,.15-.3.68.68,0,0,1,.42-.12,1.62,1.62,0,0,1,1,.29V8.11a2.58,2.58,0,0,0-1-.16,1.64,1.64,0,0,0-1.09.34,1.08,1.08,0,0,0-.42.89c0,.51.32.91,1,1.21a2.88,2.88,0,0,1,.62.36.42.42,0,0,1,.15.32.38.38,0,0,1-.16.31.81.81,0,0,1-.45.11,1.66,1.66,0,0,1-1.09-.42V12a2.17,2.17,0,0,0,1.07.24,1.88,1.88,0,0,0,1.18-.33A1.08,1.08,0,0,0,6.84,11a1.05,1.05,0,0,0-.25-.7A2.42,2.42,0,0,0,5.76,9.73ZM11,11.32a2.34,2.34,0,0,0,.33-1.26A2.32,2.32,0,0,0,11,9a1.81,1.81,0,0,0-.7-.75,2,2,0,0,0-1-.26,2.11,2.11,0,0,0-1.08.27A1.86,1.86,0,0,0,7.49,9a2.46,2.46,0,0,0-.26,1.14,2.26,2.26,0,0,0,.24,1,1.76,1.76,0,0,0,.69.74,2.06,2.06,0,0,0,1,.3l.86,1h1.21L10,12.08A1.79,1.79,0,0,0,11,11.32ZM10,11.07a.94.94,0,0,1-.76.35.92.92,0,0,1-.76-.36,1.52,1.52,0,0,1-.29-1,1.53,1.53,0,0,1,.29-1,1,1,0,0,1,.78-.37.87.87,0,0,1,.75.37,1.62,1.62,0,0,1,.27,1A1.46,1.46,0,0,1,10,11.07Z" fill="url(#sql-grad2)"/></svg>
        SQL Databases
      </router-link>
      
      <router-link 
        to="/azure/app-services" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- App Services Icon - OFFICIAL Microsoft Azure -->
        <svg class="icon mr-3" id="b70acf0a-34b4-4bdf-9024-7496043ff915" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 18"><defs><radialGradient id="e2cf8746-c9a8-4eee-86c2-4951983c6032" cx="13428.81" cy="3518.86" r="56.67" gradientTransform="translate(-2005.33 -518.83) scale(0.15)" gradientUnits="userSpaceOnUse"><stop offset="0.18" stop-color="#5ea0ef"/><stop offset="1" stop-color="#0078d4"/></radialGradient><linearGradient id="bdd213dd-d313-473c-8ff4-0133fd3a9033" x1="4.4" y1="11.48" x2="4.37" y2="7.53" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ccc"/><stop offset="1" stop-color="#fcfcfc"/></linearGradient><linearGradient id="afcc63c5-3649-4476-a742-bcb53a569f3c" x1="10.13" y1="15.45" x2="10.13" y2="11.9" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ccc"/><stop offset="1" stop-color="#fcfcfc"/></linearGradient><linearGradient id="bd873f0b-9954-4aa5-a3df-9f4c64e8729d" x1="14.18" y1="11.15" x2="14.18" y2="7.38" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ccc"/><stop offset="1" stop-color="#fcfcfc"/></linearGradient></defs><path id="ee75dd06-1aca-4f76-9d11-d05a284020ad" d="M14.21,15.72A8.5,8.5,0,0,1,3.79,2.28l.09-.06a8.5,8.5,0,0,1,10.33,13.5" fill="url(#e2cf8746-c9a8-4eee-86c2-4951983c6032)"/><path d="M6.69,7.23A13,13,0,0,1,15.6,3.65a8.47,8.47,0,0,0-1.49-1.44,14.34,14.34,0,0,0-4.69,1.1A12.54,12.54,0,0,0,5.34,6.13,2.76,2.76,0,0,1,6.69,7.23Z" fill="#fff" opacity="0.6"/><path d="M2.48,10.65a17.86,17.86,0,0,0-.83,2.62,7.82,7.82,0,0,0,.62.92c.18.23.35.44.55.65A17.94,17.94,0,0,1,3.9,11.37,2.76,2.76,0,0,1,2.48,10.65Z" fill="#fff" opacity="0.6"/><path d="M3.46,6.11a12,12,0,0,1-.69-2.94,8.15,8.15,0,0,0-1.1,1.45A12.69,12.69,0,0,0,2.24,7,2.69,2.69,0,0,1,3.46,6.11Z" fill="#f2f2f2" opacity="0.55"/><circle cx="4.38" cy="8.68" r="2.73" fill="url(#bdd213dd-d313-473c-8ff4-0133fd3a9033)"/><path d="M8.36,13.67A1.77,1.77,0,0,1,8.9,12.4a11.88,11.88,0,0,1-2.53-1.86,2.74,2.74,0,0,1-1.49.83,13.1,13.1,0,0,0,1.45,1.28A12.12,12.12,0,0,0,8.38,13.9,1.79,1.79,0,0,1,8.36,13.67Z" fill="#f2f2f2" opacity="0.55"/><path d="M14.66,13.88a12,12,0,0,1-2.76-.32.41.41,0,0,1,0,.11,1.75,1.75,0,0,1-.51,1.24,13.69,13.69,0,0,0,3.42.24A8.21,8.21,0,0,0,16,13.81,11.5,11.5,0,0,1,14.66,13.88Z" fill="#f2f2f2" opacity="0.55"/><circle cx="10.13" cy="13.67" r="1.78" fill="url(#afcc63c5-3649-4476-a742-bcb53a569f3c)"/><path d="M12.32,8.93a1.83,1.83,0,0,1,.61-1A25.5,25.5,0,0,1,8.47,3.79a16.91,16.91,0,0,1-2-2.92,7.64,7.64,0,0,0-1.09.42A18.14,18.14,0,0,0,7.53,4.47,26.44,26.44,0,0,0,12.32,8.93Z" fill="#f2f2f2" opacity="0.7"/><circle cx="14.18" cy="9.27" r="1.89" fill="url(#bd873f0b-9954-4aa5-a3df-9f4c64e8729d)"/><path d="M17.35,10.54,17,10.37l0,0-.3-.16-.06,0L16.38,10l-.07,0L16,9.8a1.76,1.76,0,0,1-.64.92c.12.08.25.15.38.22l.08.05.35.19,0,0,.86.45h0a8.63,8.63,0,0,0,.29-1.11Z" fill="#f2f2f2" opacity="0.55"/><circle cx="4.38" cy="8.68" r="2.73" fill="url(#bdd213dd-d313-473c-8ff4-0133fd3a9033)"/><circle cx="10.13" cy="13.67" r="1.78" fill="url(#afcc63c5-3649-4476-a742-bcb53a569f3c)"/></svg>
        App Services
      </router-link>
      
      <router-link 
        to="/azure/automation-accounts" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- Automation Accounts Icon - OFFICIAL Microsoft Azure -->
        <svg class="icon mr-3" id="b1565e97-e53a-44a5-9479-199d8c3c42d2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 18"><defs><linearGradient id="ec4358fa-c977-42e2-a7ab-994b5de56830" x1="9" y1="177.9" x2="9" y2="160.1" gradientTransform="translate(0 -160)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#0078d4"/><stop offset="0.064" stop-color="#0a7cd7"/><stop offset="0.338" stop-color="#2e8ce1"/><stop offset="0.594" stop-color="#4897e9"/><stop offset="0.822" stop-color="#589eed"/><stop offset="1" stop-color="#5ea0ef"/></linearGradient><linearGradient id="aae9e42c-091e-4dc7-8bec-a93418af93c4" x1="-26.189" y1="-295.6" x2="-26.189" y2="-311.105" gradientTransform="translate(39.425 321.61) scale(1.156 1.029)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fea11b"/><stop offset="0.284" stop-color="#fea51a"/><stop offset="0.547" stop-color="#feb018"/><stop offset="0.8" stop-color="#ffc314"/><stop offset="1" stop-color="#ffd70f"/></linearGradient></defs><path d="M17.9,10V8l-.3-.1-2.2-.7-.6-1.4L16,3.4,14.5,2l-.3.1-2,1-1.4-.6L10,.1H8L7.8.4,7.1,2.6l-1.4.5L3.4,2,2,3.5l.1.3,1,2L2.6,7.2.1,8v2l.3.1,2.2.7.6,1.4L2,14.6,3.5,16l.3-.1,2-1,1.4.6L8,17.9h2l.1-.3.7-2.2,1.4-.6,2.3,1.1,1.4-1.4-.1-.3-1-2,.6-1.4ZM9,12.9A3.842,3.842,0,0,1,5.1,9,3.842,3.842,0,0,1,9,5.1,3.842,3.842,0,0,1,12.9,9h0A3.842,3.842,0,0,1,9,12.9Z" fill="url(#ec4358fa-c977-42e2-a7ab-994b5de56830)"/><path d="M8.5,10.5H4.9a.215.215,0,0,1-.2-.2v-.1L9,1.7c0-.1.1-.1.2-.1h4.2a.215.215,0,0,1,.2.2v.1L8.5,8.6h4.9a.215.215,0,0,1,.2.2.1.1,0,0,1-.1.1L5.3,17.4c-.1,0-.6.5-.4-.2h0Z" fill="url(#aae9e42c-091e-4dc7-8bec-a93418af93c4)"/></svg>
        Automation Accounts
      </router-link>
      
      <div :class="isDark ? 'border-t border-gray-700 my-4' : 'border-t border-gray-200 my-4'"></div>
      
      <!-- Settings -->
      <router-link 
        to="/settings" 
        :class="navLinkClass"
        :active-class="navLinkActiveClass"
      >
        <!-- User Settings Icon - OFFICIAL Microsoft Azure -->
        <svg class="icon mr-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 18"><defs><linearGradient id="a8e2a822-3d11-419e-851a-77f3b59c6412" x1="6.85" y1="7.226" x2="6.85" y2="18.562" gradientUnits="userSpaceOnUse"><stop offset="0.225" stop-color="#32d4f5"/><stop offset="0.473" stop-color="#31d1f3"/><stop offset="0.888" stop-color="#22a5cb"/><stop offset="0.999" stop-color="#198ab3"/><stop offset="1" stop-color="#198ab3"/></linearGradient><linearGradient id="a2fafb19-725d-413a-bceb-19447c64feab" x1="6.563" y1="1.149" x2="7.391" y2="11.442" gradientUnits="userSpaceOnUse"><stop offset="0.225" stop-color="#32d4f5"/><stop offset="0.473" stop-color="#31d1f3"/><stop offset="0.888" stop-color="#22a5cb"/><stop offset="0.999" stop-color="#198ab3"/><stop offset="1" stop-color="#198ab3"/></linearGradient></defs><g id="b89ba70f-40d4-49bf-9168-1914828bbd51"><g><path d="M17.977,9.2V7.788l-.2-.074-1.511-.5-.4-.966.768-1.634-.991-.991-.2.1-1.412.718-.966-.4-.619-1.709H11.041l-.074.2-.5,1.511-.966.4L7.9,3.676l-.991.991.1.2.718,1.412-.4.966-1.734.619V9.274l.2.074,1.511.5.4.966L6.93,12.445l.99.99.2-.1,1.412-.718.966.4.619,1.709h1.412l.075-.2.495-1.511.966-.4,1.635.768.991-.991-.1-.2-.718-1.412.4-.966Zm-6.193,2.049A2.718,2.718,0,1,1,14.5,8.531,2.715,2.715,0,0,1,11.784,11.249Z" fill="#0078d4"/><g><path d="M12.459,16.516a1.215,1.215,0,0,0,1.218-1.21,1.413,1.413,0,0,0-.008-.146c-.478-3.816-2.655-6.923-6.808-6.923C2.635,8.237.455,10.868.03,15.17a1.22,1.22,0,0,0,1.089,1.339,1,1,0,0,0,.122.007Z" fill="url(#a8e2a822-3d11-419e-851a-77f3b59c6412)"/><path d="M6.926,9.141a3.808,3.808,0,0,1-2.073-.61l2.052,5.361L8.943,8.567A3.81,3.81,0,0,1,6.926,9.141Z" fill="#fff" opacity="0.8"/><circle cx="6.898" cy="5.313" r="3.829" fill="url(#a2fafb19-725d-413a-bceb-19447c64feab)"/></g></g></g></svg>
        Settings
      </router-link>
    </nav>
    
    <!-- Logout Button (Footer) -->
    <div class="p-4 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
      <button
        @click="handleLogout"
        :class="[
          'w-full flex items-center px-4 py-3 rounded-lg transition-colors font-semibold',
          isDark 
            ? 'text-red-400 hover:bg-red-900/30 border border-red-900/50' 
            : 'text-red-600 hover:bg-red-50 border border-red-200'
        ]"
      >
        <svg class="icon mr-3" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z" fill="currentColor"/>
        </svg>
        Logout
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const router = useRouter()
const { logout } = useAuth()

// Computed classes for navigation links
const navLinkClass = computed(() => {
  return props.isDark 
    ? 'flex items-center px-4 py-3 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors'
    : 'flex items-center px-4 py-3 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors'
})

const navLinkActiveClass = computed(() => {
  return props.isDark
    ? 'bg-blue-900/50 text-blue-400 font-semibold'
    : 'bg-blue-100 text-blue-700 font-semibold'
})

const handleLogout = async () => {
  await logout()
  router.push('/login')
}
</script>

<style scoped>
.icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.logo-specter {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
