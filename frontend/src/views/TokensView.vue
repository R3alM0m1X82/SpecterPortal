<template>
  <div :class="['p-8 w-full', isDark ? 'bg-gray-900' : '']">
    <div class="flex items-center justify-between mb-6">
      <h1 :class="['text-3xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">Tokens</h1>
      <div class="flex items-center space-x-4">
        <span :class="isDark ? 'text-gray-400' : 'text-gray-600'">
          {{ filteredTokens.length }} / {{ tokens.length }} token(s)
        </span>
        <button 
          v-if="selectedTokens.length > 0"
          @click="deleteSelected" 
          class="btn btn-danger"
        >
          🗑️ Delete Selected ({{ selectedTokens.length }})
        </button>
        <button 
          @click="deleteExpired" 
          :disabled="deletingExpired"
          :class="['btn', isDark ? 'btn-warning-outline-dark' : 'btn-warning-outline', deletingExpired ? 'opacity-50 cursor-not-allowed' : '']"
        >
          <span v-if="deletingExpired">⏳ Deleting...</span>
          <span v-else>⏰ Delete Expired</span>
        </button>
        <button 
          @click="deleteAll" 
          :disabled="deletingAll"
          :class="['btn', isDark ? 'btn-danger-outline-dark' : 'btn-danger-outline', deletingAll ? 'opacity-50 cursor-not-allowed' : '']"
        >
          <span v-if="deletingAll">⏳ Deleting...</span>
          <span v-else>🗑️ Delete All</span>
        </button>
        <button @click="loadTokens" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          🔄 Refresh
        </button>
        <router-link to="/import" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          📥 Import JSON
        </router-link>
        <button @click="openImportJwtModal" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          🔑 Import JWT
        </button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-5 gap-6 mb-6">
      <!-- Total Tokens -->
      <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-base font-semibold" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Total Tokens</p>
            <p class="text-3xl font-bold mt-1" :class="isDark ? 'text-white' : 'text-gray-800'">
              {{ tokens.length }}
            </p>
          </div>
          <!-- tokens.svg -->
          <div class="flex-shrink-0 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="w-10 h-10"><g id="FLAT"><path d="M216,288v48c0,53.01929,60.88928,96,136,96s136-42.98071,136-96V288Z" style="fill:#e5707f"/><path d="M440,409.188a125.38379,125.38379,0,0,0,16-11.335V344H440Z" style="fill:#f78f9c"/><path d="M392,427.77686q8.23325-1.78564,16-4.26734V368H392Z" style="fill:#f78f9c"/><path d="M344,431.83032c2.64783.1084,5.3136.16968,8,.16968s5.35217-.06128,8-.16968V368H344Z" style="fill:#f78f9c"/><path d="M296,423.50952q7.75287,2.476,16,4.26734V368H296Z" style="fill:#f78f9c"/><path d="M248,397.853a125.38379,125.38379,0,0,0,16,11.335V344H248Z" style="fill:#f78f9c"/><ellipse cx="352" cy="288" rx="136" ry="96" style="fill:#f78f9c"/><path d="M352,360c-29.23975,0-56.84521-7.07812-77.73193-19.93164C252.16992,326.46973,240,307.97754,240,288s12.16992-38.46973,34.26807-52.06836C295.15479,223.07812,322.76025,216,352,216s56.84521,7.07812,77.73193,19.93164C451.83008,249.53027,464,268.02246,464,288s-12.16992,38.46973-34.26807,52.06836C408.84521,352.92188,381.23975,360,352,360Zm0-128c-26.31934,0-50.94678,6.23535-69.34619,17.55859C265.46582,260.13574,256,273.78711,256,288s9.46582,27.86426,26.65381,38.44141C301.05322,337.76465,325.68066,344,352,344s50.94678-6.23535,69.34619-17.55859C438.53418,315.86426,448,302.21289,448,288s-9.46582-27.86426-26.65381-38.44141C402.94678,238.23535,378.31934,232,352,232Z" style="fill:#f9acb9"/><path d="M24,336v56c0,53.01929,60.88928,96,136,96s136-42.98071,136-96V336Z" style="fill:#3f589e"/><path d="M248,465.188a125.38379,125.38379,0,0,0,16-11.335V392H248Z" style="fill:#576cd3"/><path d="M200,483.77686q8.23325-1.78564,16-4.26734V424H200Z" style="fill:#576cd3"/><path d="M152,487.83032c2.64783.1084,5.3136.16968,8,.16968s5.35217-.06128,8-.16968V432H152Z" style="fill:#576cd3"/><path d="M104,479.50952q7.75287,2.476,16,4.26734V424H104Z" style="fill:#576cd3"/><path d="M56,453.853a125.38379,125.38379,0,0,0,16,11.335V400H56Z" style="fill:#576cd3"/><ellipse cx="160" cy="336" rx="136" ry="104" style="fill:#576cd3"/><path d="M108.52783,317.45117l-9.05566-13.18945C114.52393,293.92676,136.58545,288,160,288v16C139.74023,304,120.97949,308.90332,108.52783,317.45117Z" style="fill:#7f9ae5"/><path d="M160,384c-44.85986,0-80-21.084-80-48a31.225,31.225,0,0,1,1.92676-10.74609l15.02734,5.49218A15.28682,15.28682,0,0,0,96,336c0,7.53809,6.18652,15.29883,16.97314,21.291C125.40381,364.19727,142.105,368,160,368c2.50488,0,5.03174-.07715,7.51025-.22949l.9795,15.9707C165.687,383.91309,162.83057,384,160,384Z" style="fill:#7f9ae5"/><path d="M194.12891,379.55371l-4.25782-15.42383C210.28467,358.49512,224,347.19043,224,336a15.28682,15.28682,0,0,0-.9541-5.25391l15.02734-5.49218A31.225,31.225,0,0,1,240,336C240,355.05371,222.42334,371.74219,194.12891,379.55371Z" style="fill:#7f9ae5"/><path d="M60.31152,372.665C52.25732,361.44531,48,348.7666,48,336c0-37.55762,35.65576-69.61914,86.709-77.96875l2.582,15.791c-20.9668,3.42871-39.88233,11.68261-53.26123,23.24023C70.92627,308.38281,64,321.84766,64,336c0,9.5332,3.13232,18.72949,9.30957,27.335Z" style="fill:#7f9ae5"/><path d="M160,416c-25.44922,0-49.40674-5.88477-69.28223-17.01953l7.81934-13.959C115.7793,394.68066,137.60742,400,160,400c41.07861,0,77.63135-17.53711,90.957-43.6377l14.25,7.2754C249.21777,394.957,206.938,416,160,416Z" style="fill:#7f9ae5"/><path d="M296.00012,24H256V328h40.00012A152,152,0,0,0,448,176v-.00024A151.9999,151.9999,0,0,0,296.00012,24Z" style="fill:#00a16c"/><path d="M406.83887,72H352V88h67.95026A152.7461,152.7461,0,0,0,406.83887,72Z" style="fill:#00b378"/><path d="M437.34839,120H384v16h58.67A150.82364,150.82364,0,0,0,437.34839,120Z" style="fill:#00b378"/><path d="M400,184h47.791q.20608-3.97411.209-8v-.00024q0-4.0254-.209-7.99976H400Z" style="fill:#00b378"/><path d="M442.67,216H384v16h53.34833A150.82393,150.82393,0,0,0,442.67,216Z" style="fill:#00b378"/><path d="M419.9502,264H360v16h46.83881A152.7461,152.7461,0,0,0,419.9502,264Z" style="fill:#00b378"/><circle cx="256" cy="176" r="152" style="fill:#00b378"/><path d="M168.97461,269.86523A128.01445,128.01445,0,0,1,319.90576,65.07129l-7.999,13.85742A112.01077,112.01077,0,0,0,179.85547,258.13477Z" style="fill:#46c89d"/><path d="M256,304a128.27777,128.27777,0,0,1-59.73877-14.76855l7.47754-14.14454a112.01377,112.01377,0,0,0,134.396-175.23144l11.73046-10.88086A128.00041,128.00041,0,0,1,256,304Z" style="fill:#46c89d"/><polygon points="328 216 328 136 256 96 184 136 184 216 256 256 328 216" style="fill:#76d6b4"/><path d="M304,192H288V164.5293l-32.3501-19.41016-28.07226,14.03613-7.15528-14.31054,32-16a7.99923,7.99923,0,0,1,7.69385.29492l40,24A8.00153,8.00153,0,0,1,304,160Z" style="fill:#46c89d"/><path d="M352,480a227.21078,227.21078,0,0,1-41.46387-3.77344l2.92774-15.73047A211.12073,211.12073,0,0,0,352,464c34.07129,0,67.16064-8.15137,93.17236-22.95312l7.91309,13.90624C424.70068,471.10449,388.80127,480,352,480Z" style="fill:#ffc7d3"/><path d="M468.78076,444.72559l-9.56152-12.82813A113.70147,113.70147,0,0,0,474.167,418.6377l11.667,10.94921A129.74779,129.74779,0,0,1,468.78076,444.72559Z" style="fill:#ffc7d3"/><path d="M74.54443,145.32422l-15.77929-2.64844c.937-5.584,2.12646-11.19238,3.53613-16.66992l15.49512,3.98828C76.50049,135.03027,75.40625,140.18848,74.54443,145.32422Z" style="fill:#bdecdc"/><path d="M62.30127,225.99414A200.70085,200.70085,0,0,1,56,176c0-5.54688.23-11.15137.68408-16.65723l15.94629,1.31446C72.21191,165.72754,72,170.88965,72,176a184.68568,184.68568,0,0,0,5.79639,46.00586Z" style="fill:#bdecdc"/><path d="M64,32h0a.99539.99539,0,0,0-.96947.7854A40.04767,40.04767,0,0,1,32.78535,63.02219.9954.9954,0,0,0,32,63.99166v.01668a.9954.9954,0,0,0,.78535.96947A40.04767,40.04767,0,0,1,63.03053,95.2146.99539.99539,0,0,0,64,96h.00834a.9954.9954,0,0,0,.96947-.78535A40.04767,40.04767,0,0,1,95.2146,64.96947.99539.99539,0,0,0,96,64v-.00834a.9954.9954,0,0,0-.78535-.96947A40.04767,40.04767,0,0,1,64.96947,32.7854.99539.99539,0,0,0,64,32Z" style="fill:#46c89d"/></g></svg>
          </div>
        </div>
      </div>
      
      <!-- Active Token -->
      <div class="rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow" 
           :class="isDark ? 'bg-gray-800' : 'bg-white'"
           @click="activeTokenId ? scrollToToken(activeTokenId) : null">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <p class="text-base font-semibold mb-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Active Token</p>
            <p class="text-3xl font-bold" :class="hasActiveToken ? 'text-green-500' : (isDark ? 'text-gray-500' : 'text-gray-400')">
              {{ hasActiveToken ? `#${activeTokenId}` : 'None' }}
            </p>
            <!-- Analyze Button (centered) -->
            <div v-if="hasActiveToken" class="flex justify-center mt-3">
              <button 
                @click.stop="showAnalyzeModal = true" 
                class="text-sm px-3 py-1.5 rounded transition-colors font-medium"
                :class="isDark ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-blue-500 text-white hover:bg-blue-600'"
              >
                🔍 Analyze Active Token
              </button>
            </div>
          </div>
          <!-- jwt.svg -->
          <div class="flex-shrink-0 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" class="w-10 h-10"><polygon fill="#546e7a" points="21.906,31.772 24.507,29.048 27.107,31.772 27.107,43 21.906,43"/><polygon fill="#f50057" points="17.737,29.058 21.442,28.383 21.945,32.115 15.345,41.199 11.138,38.141"/><polygon fill="#d500f9" points="15.962,24.409 19.355,26.041 17.569,29.356 6.89,32.825 5.283,27.879"/><polygon fill="#29b6f6" points="17.256,19.607 19.042,22.922 15.649,24.554 4.97,21.084 6.577,16.137"/><polygon fill="#00e5ff" points="21.126,16.482 20.623,20.214 16.918,19.539 10.318,10.455 14.526,7.398"/><polygon fill="#546e7a" points="26.094,16.228 23.493,18.952 20.893,16.228 20.893,5 26.094,5"/><polygon fill="#f50057" points="30.262,18.943 26.558,19.618 26.055,15.886 32.654,6.802 36.862,9.859"/><polygon fill="#d500f9" points="32.039,23.59 28.645,21.958 30.431,18.643 41.11,15.174 42.717,20.12"/><polygon fill="#29b6f6" points="30.744,28.393 28.958,25.078 32.351,23.447 43.03,26.916 41.423,31.863"/><polygon fill="#00e5ff" points="26.874,31.518 27.378,27.786 31.082,28.461 37.682,37.545 33.474,40.602"/></svg>
          </div>
        </div>
      </div>
      
      <!-- Refresh Tokens -->
      <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-base font-semibold" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Refresh Tokens</p>
            <p class="text-3xl font-bold text-blue-500 mt-1">
              {{ refreshTokensCount }}
            </p>
          </div>
          <!-- recycling.svg -->
          <div class="flex-shrink-0 flex items-center">
            <svg id="Capa_1" enable-background="new 0 0 512 512" viewBox="0 0 512 512" class="w-10 h-10" xmlns="http://www.w3.org/2000/svg"><g><g><path d="m76 256c0 99.411 80.589 180 180 180l57.252-172.791-57.252-187.209c-99.411 0-180 80.589-180 180z" fill="#fff4f4"/><path d="m256 76v360c99.411 0 180-80.589 180-180s-80.589-180-180-180z" fill="#e5e9f2"/></g><path d="m256 0 34.386 39.945-34.386 38.125c-49.06 0-93.54 19.95-125.76 52.17l-54.24-14.516-1.02-40.744c46.33-46.32 110.33-74.98 181.02-74.98z" fill="#b5f84e"/><path d="m437.02 74.98-8.303 55.26h-46.957c-32.22-32.22-76.7-52.17-125.76-52.17v-78.07c70.69 0 134.69 28.66 181.02 74.98z" fill="#61d94c"/><path d="m512 256-37.551 25.457-40.519-25.457c0-49.06-19.95-93.54-52.17-125.76l55.26-55.26c46.32 46.33 74.98 110.33 74.98 181.02z" fill="#02b663"/><path d="m512 256c0 70.69-28.66 134.69-74.98 181.02l-51.39-15.3-3.87-39.96c32.22-32.22 52.17-76.7 52.17-125.76z" fill="#61d94c"/><path d="m437.02 437.02c-46.33 46.32-110.33 74.98-181.02 74.98l-26.465-40.811 26.465-37.259c49.06 0 93.54-19.95 125.76-52.17z" fill="#02b663"/><path d="m256 433.93v78.07c-70.69 0-134.69-28.66-181.02-74.98l16.78-55.26h38.48c32.22 32.22 76.7 52.17 125.76 52.17z" fill="#61d94c"/><path d="m130.24 381.76-55.26 55.26c-46.32-46.33-74.98-110.33-74.98-181.02l38.291-25.567 39.779 25.567c0 49.06 19.95 93.54 52.17 125.76z" fill="#b5f84e"/><path d="m130.24 130.24c-32.22 32.22-52.17 76.7-52.17 125.76h-78.07c0-70.69 28.66-134.69 74.98-181.02z" fill="#61d94c"/><g><path d="m231.665 170.056 19.461-19.46-21.213-21.213-55.674 55.673 55.674 55.674 21.213-21.213-19.461-19.461h24.335l11.11-15-11.11-15z" fill="#a7eaf9"/><path d="m307.921 248.791h30c0-43.415-35.32-78.735-78.734-78.735h-3.187v30h3.187c26.872 0 48.734 21.862 48.734 48.735z" fill="#72bbff"/><path d="m252.813 311.944c-26.872 0-48.734-21.862-48.734-48.735h-30c0 43.415 35.32 78.735 78.734 78.735h3.187l11.11-15-11.11-15z" fill="#a7eaf9"/><path d="m260.874 292.483 19.461 19.461h-24.335v30h24.335l-19.461 19.46 21.213 21.213 55.674-55.673-55.674-55.674z" fill="#72bbff"/></g></g></svg>
          </div>
        </div>
      </div>
      
      <!-- Office Master Tokens -->
      <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-base font-semibold" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Office Master</p>
            <p class="text-3xl font-bold text-yellow-500 mt-1">
              {{ officeMasterCount }}
            </p>
          </div>
          <!-- master.svg -->
          <div class="flex-shrink-0 flex items-center">
            <svg viewBox="0 0 128 128" class="w-10 h-10" xmlns="http://www.w3.org/2000/svg"><g><circle cx="64" cy="63.997" fill="#ffc839" r="62.25" transform="matrix(.16 -.987 .987 .16 -9.422 116.919)"/><g fill="#ff9100"><path d="m62.25 1.791v14.956a1.75 1.75 0 0 0 3.5 0v-14.956c-.583-.016-1.163-.044-1.75-.044s-1.167.028-1.75.044z"/><path d="m64 109.5a1.751 1.751 0 0 0 -1.75 1.75v14.95c.583.016 1.163.044 1.75.044s1.167-.028 1.75-.044v-14.953a1.751 1.751 0 0 0 -1.75-1.747z"/><path d="m96.173 29.349a1.75 1.75 0 0 0 2.475 2.475l10.577-10.577q-1.2-1.272-2.474-2.475z"/><path d="m29.352 96.17-10.577 10.578q1.2 1.272 2.474 2.474l10.578-10.577a1.75 1.75 0 1 0 -2.475-2.475z"/><path d="m126.206 62.247h-14.956a1.75 1.75 0 0 0 0 3.5h14.956c.016-.583.044-1.163.044-1.75s-.028-1.167-.044-1.75z"/><path d="m16.75 62.247h-14.956c-.016.583-.044 1.163-.044 1.753s.028 1.167.044 1.75h14.956a1.75 1.75 0 0 0 0-3.5z"/><path d="m96.173 96.17a1.751 1.751 0 0 0 0 2.475l10.578 10.577q1.27-1.2 2.474-2.474l-10.577-10.578a1.751 1.751 0 0 0 -2.475 0z"/><path d="m21.249 18.772q-1.272 1.2-2.474 2.475l10.577 10.577a1.75 1.75 0 0 0 2.475-2.475z"/></g><circle cx="64" cy="63.997" fill="#2d3c6b" r="47.25"/><g fill="#73c3f9"><path d="m83.312 88.313h-38.625l-5.004-32.875 16.311 15.011 8.006-15.011 8.006 15.011 16.31-15.011z"/><circle cx="64" cy="44.75" r="5.063"/><circle cx="88.316" cy="44.75" r="5.062"/><circle cx="39.683" cy="44.75" r="5.063"/></g></g></svg>
          </div>
        </div>
      </div>
      
      <!-- Expired Tokens -->
      <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-base font-semibold" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Expired Tokens</p>
            <p class="text-3xl font-bold text-red-500 mt-1">
              {{ expiredTokensCount }}
            </p>
          </div>
          <!-- delete.svg -->
          <div class="flex-shrink-0 flex items-center">
            <svg clip-rule="evenodd" fill-rule="evenodd" viewBox="0 0 1707 1707" class="w-10 h-10" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><defs><linearGradient id="id0" gradientUnits="userSpaceOnUse" x1="530.469" x2="1176.19" y1="853.331" y2="853.331"><stop offset="0" stop-color="#d0054a"/><stop offset="1" stop-color="#ff377c"/></linearGradient><linearGradient id="id1" gradientUnits="userSpaceOnUse" x1="124.98" x2="1581.69" y1="853.331" y2="853.331"><stop offset="0" stop-color="#e67f00"/><stop offset=".74902" stop-color="#f2980c"/><stop offset="1" stop-color="#ffb119"/></linearGradient><linearGradient id="id2" gradientUnits="userSpaceOnUse" x1="0" x2="1706.66" y1="853.331" y2="853.331"><stop offset="0" stop-color="#e6a800"/><stop offset=".490196" stop-color="#f2c110"/><stop offset="1" stop-color="#ffda20"/></linearGradient><linearGradient id="id3" gradientUnits="userSpaceOnUse" x1="669.331" x2="1036.98" y1="853.85" y2="853.85"><stop offset="0" stop-color="#e6e6e6"/><stop offset=".478431" stop-color="#f2f2f2"/><stop offset="1" stop-color="#fff"/></linearGradient><linearGradient id="id4" gradientUnits="userSpaceOnUse" x1="669.331" x2="1038.37" y1="853.157" y2="853.157"><stop offset="0" stop-color="#e6e6e6"/><stop offset="1" stop-color="#fff"/></linearGradient></defs><g id="Layer_x0020_1"><g id="_482148696"><g><path d="m853 0c-471 0-853 382-853 853 0 472 382 854 853 854 472 0 854-382 854-854 0-471-382-853-854-853z" fill="url(#id2)"/><path d="m853 1582c-31 0-57-25-57-57 0-31 26-57 57-57 169 0 323-70 434-181s181-265 181-434c0-75-13-148-38-214-25-70-62-132-109-188-21-23-18-58 5-80 24-20 60-17 81 7 55 65 100 140 130 221 29 79 45 165 45 252 0 202-82 384-213 515-133 134-315 216-516 216zm215-1425c30 8 46 42 37 71-8 30-41 47-70 37-28-8-59-15-89-19-31-4-60-7-92-7-169 0-324 69-433 180-113 111-181 266-181 434 0 76 14 150 41 218 26 69 65 133 113 189 21 23 18 58-5 80-24 21-60 18-81-5-59-66-105-141-136-224-32-82-47-167-47-258 0-202 81-384 212-516 132-131 314-212 516-212 37 0 73 1 108 8 36 4 72 13 107 24zm-624 1300c-26-18-32-53-15-79 18-27 53-34 79-16 28 20 57 36 89 50 31 14 63 25 95 34 30 8 48 40 41 69-8 31-40 49-69 40-39-9-77-23-113-41-37-16-72-35-107-57z" fill="url(#id1)"/><path d="m593 530h519c35 0 64 28 64 63v519c0 35-29 64-64 64h-519c-35 0-63-29-63-64v-519c0-35 28-63 63-63z" fill="url(#id0)"/><path d="m940 686c22-22 58-22 81 0 23 24 23 58 0 81l-254 252c-23 24-59 24-81 0-22-22-22-58 0-80z" fill="url(#id4)"/><path d="m1019 940c24 22 24 58 0 81-22 23-58 23-80 0l-253-254c-22-23-22-59 0-81 24-22 58-22 81 0z" fill="url(#id3)"/></g></g></g></svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Authentication Button -->
    <div :class="['mb-6 rounded-lg shadow-md p-4', isDark ? 'bg-gray-800' : 'bg-white']">
      <div class="flex items-center justify-between">
        <div>
          <h3 :class="['font-semibold', isDark ? 'text-gray-100' : 'text-gray-800']">
            🔐 Get New Token
          </h3>
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-500']">
            Authenticate via Device Code Flow or Username/Password
          </p>
        </div>
        <button 
          @click="authModalOpen = true"
          class="btn btn-primary"
        >
          Authenticate
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div :class="['mb-6 rounded-lg shadow-md p-4', isDark ? 'bg-gray-800' : 'bg-white']">
      <!-- Scope Search -->
      <div class="mb-4">
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
          🔍 Search by Audience, Scope or UPN
        </label>
        <div class="flex gap-3">
          <input
            v-model="scopeSearch"
            type="text"
            placeholder="Enter audience, scope or UPN to search (e.g., graph.microsoft.com, chat.read, user@domain.com)..."
            :class="[
              'flex-1 px-4 py-2 rounded-lg border transition-colors',
              isDark 
                ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500' 
                : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500'
            ]"
          />
          <button
            @click="clearScopeSearch"
            :class="[
              'px-6 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap',
              scopeSearch
                ? 'bg-red-600 text-white hover:bg-red-700'
                : isDark ? 'bg-gray-700 text-gray-400 cursor-not-allowed' : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            ]"
            :disabled="!scopeSearch"
          >
            🗑️ Clear
          </button>
        </div>
        <p v-if="scopeSearch" :class="['text-xs mt-1', isDark ? 'text-gray-400' : 'text-gray-500']">
          Filtering {{ filteredTokens.length }} token(s) matching "{{ scopeSearch }}" in audience, scope or UPN
        </p>
      </div>

      <!-- Token Type Filters + Analyze Button -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span :class="['text-sm font-medium mr-2', isDark ? 'text-gray-300' : 'text-gray-700']">Filter by type:</span>
          <button
            @click="filterType = 'all'"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-semibold transition-colors',
              filterType === 'all'
                ? 'bg-blue-600 text-white'
                : isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            ]"
          >
            All Tokens
          </button>
          <button
            @click="filterType = 'access_token'"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-semibold transition-colors',
              filterType === 'access_token'
                ? 'bg-green-600 text-white'
                : isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            ]"
          >
            🔑 Access Tokens
          </button>
          <button
            @click="filterType = 'refresh_token'"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-semibold transition-colors',
              filterType === 'refresh_token'
                ? 'bg-purple-600 text-white'
                : isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            ]"
          >
            🔄 Refresh Tokens
          </button>
          <button
            @click="filterType = 'ngc_token'"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-semibold transition-colors',
              filterType === 'ngc_token'
                ? 'bg-orange-600 text-white'
                : isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            ]"
          >
            🛡️ NGC Tokens
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
      <p :class="['mt-4', isDark ? 'text-gray-400' : 'text-gray-500']">Loading tokens...</p>
    </div>
    
    <div v-else-if="filteredTokens.length === 0 && tokens.length === 0" :class="['text-center py-12 rounded-lg shadow-md', isDark ? 'bg-gray-800' : 'bg-white']">
      <div class="flex justify-center mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="96px" height="96px">
          <polygon fill="#546e7a" points="21.906,31.772 24.507,29.048 27.107,31.772 27.107,43 21.906,43"/>
          <polygon fill="#f50057" points="17.737,29.058 21.442,28.383 21.945,32.115 15.345,41.199 11.138,38.141"/>
          <polygon fill="#d500f9" points="15.962,24.409 19.355,26.041 17.569,29.356 6.89,32.825 5.283,27.879"/>
          <polygon fill="#29b6f6" points="17.256,19.607 19.042,22.922 15.649,24.554 4.97,21.084 6.577,16.137"/>
          <polygon fill="#00e5ff" points="21.126,16.482 20.623,20.214 16.918,19.539 10.318,10.455 14.526,7.398"/>
          <polygon fill="#546e7a" points="26.094,16.228 23.493,18.952 20.893,16.228 20.893,5 26.094,5"/>
          <polygon fill="#f50057" points="30.262,18.943 26.558,19.618 26.055,15.886 32.654,6.802 36.862,9.859"/>
          <polygon fill="#d500f9" points="32.039,23.59 28.645,21.958 30.431,18.643 41.11,15.174 42.717,20.12"/>
          <polygon fill="#29b6f6" points="30.744,28.393 28.958,25.078 32.351,23.447 43.03,26.916 41.423,31.863"/>
          <polygon fill="#00e5ff" points="26.874,31.518 27.378,27.786 31.082,28.461 37.682,37.545 33.474,40.602"/>
        </svg>
      </div>
      <h2 :class="['text-2xl font-semibold mb-2', isDark ? 'text-gray-100' : 'text-gray-800']">No Tokens Yet</h2>
      <p :class="['mb-6', isDark ? 'text-gray-400' : 'text-gray-500']">Import tokens or authenticate to get started</p>
      <div class="flex justify-center space-x-4">
        <button @click="authModalOpen = true" class="btn btn-primary">
          🔐 Authenticate
        </button>
        <router-link to="/import" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          📥 Import Tokens
        </router-link>
      </div>
    </div>

    <div v-else-if="filteredTokens.length === 0" :class="['text-center py-12 rounded-lg shadow-md', isDark ? 'bg-gray-800' : 'bg-white']">
      <div class="text-6xl mb-4">🔍</div>
      <h2 :class="['text-2xl font-semibold mb-2', isDark ? 'text-gray-100' : 'text-gray-800']">No Tokens Match Filter</h2>
      <p :class="['mb-6', isDark ? 'text-gray-400' : 'text-gray-500']">Try selecting a different filter</p>
      <button @click="filterType = 'all'" class="btn btn-primary">
        Show All Tokens
      </button>
    </div>
    
    <div v-else>
      <!-- Select All -->
      <div :class="['mb-4 p-3 rounded-lg flex items-center', isDark ? 'bg-gray-800' : 'bg-gray-50']">
        <input
          type="checkbox"
          :checked="allSelected"
          @change="toggleSelectAll"
          class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
        />
        <label :class="['ml-2 text-sm font-medium', isDark ? 'text-gray-300' : 'text-gray-700']">
          Select All ({{ filteredTokens.length }} visible)
        </label>
      </div>
      
      <!-- Tokens Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="token in filteredTokens" :key="token.id" :data-token-id="token.id" class="relative">
          <input
            type="checkbox"
            :checked="selectedTokens.includes(token.id)"
            @change="toggleSelect(token.id)"
            class="absolute top-4 left-4 w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500 z-10"
          />
          <TokenCard
            :token="token"
            :isDark="isDark"
            :highlight-text="scopeSearch"
            @activate="activateToken"
            @delete="deleteToken"
            @use-refresh="openRefreshModal"
            class="ml-8"
          />
        </div>
      </div>
    </div>

    <!-- Refresh Token Modal -->
    <RefreshTokenModal
      :isOpen="refreshModalOpen"
      :token="selectedRefreshToken"
      :isDark="isDark"
      @close="closeRefreshModal"
      @success="handleRefreshSuccess"
    />

    <!-- Authentication Modal -->
    <AuthModal
      :isOpen="authModalOpen"
      :isDark="isDark"
      @close="authModalOpen = false"
      @success="handleAuthSuccess"
    />

    <!-- Import JWT Modal -->
    <Teleport to="body">
      <div v-if="importJwtModalOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div 
          class="w-full max-w-2xl mx-4 rounded-lg shadow-xl"
          :class="isDark ? 'bg-gray-800' : 'bg-white'"
        >
          <div class="p-6 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-xl font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">
                  Import JWT Access Token
                </h2>
                <p class="mt-1 text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                  Paste a raw JWT access token (eyJ...)
                </p>
              </div>
              <button
                @click="closeImportJwtModal"
                class="p-2 rounded-lg transition-colors"
                :class="isDark ? 'hover:bg-gray-700 text-gray-400' : 'hover:bg-gray-100 text-gray-500'"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium mb-2" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                JWT Token
              </label>
              <textarea
                v-model="importJwtData"
                rows="6"
                class="w-full px-4 py-3 rounded-lg border font-mono text-sm"
                :class="isDark 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400'"
                placeholder="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik1jN2wzSXo5..."
              ></textarea>
            </div>
            
            <!-- JWT Preview -->
            <div v-if="jwtPreview" class="p-4 rounded-lg" :class="isDark ? 'bg-gray-700' : 'bg-gray-100'">
              <h4 class="text-sm font-medium mb-2" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Token Preview
              </h4>
              <div class="space-y-1 text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
                <p v-if="jwtPreview.upn"><span class="font-medium">UPN:</span> {{ jwtPreview.upn }}</p>
                <p v-if="jwtPreview.aud"><span class="font-medium">Audience:</span> {{ jwtPreview.aud }}</p>
                <p v-if="jwtPreview.scp"><span class="font-medium">Scopes:</span> {{ jwtPreview.scp }}</p>
                <p v-if="jwtPreview.exp"><span class="font-medium">Expires:</span> {{ formatJwtExpiry(jwtPreview.exp) }}</p>
              </div>
            </div>
            
            <!-- Error message -->
            <div v-if="jwtError" class="p-3 rounded-lg bg-red-500/20 text-red-400 text-sm">
              {{ jwtError }}
            </div>
          </div>
          
          <div class="p-6 border-t flex justify-end gap-3" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
            <button
              @click="closeImportJwtModal"
              class="px-4 py-2 rounded-lg transition-colors"
              :class="isDark ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'"
            >
              Cancel
            </button>
            <button
              @click="importJwt"
              :disabled="!importJwtData.trim() || !!jwtError || importingJwt"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ importingJwt ? 'Importing...' : 'Import' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Analyze Token Modal -->
    <AnalyzeTokenModal 
      :show="showAnalyzeModal" 
      :isDark="isDark" 
      @close="showAnalyzeModal = false" 
    />
  </div>
</template>

<style scoped>
/* Fix scope overflow in token cards - Sprint 5.4 */
:deep(.token-scope),
:deep(.scope-badge),
:deep([class*="scope"]) {
  max-width: 100%;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  line-height: 1.4;
}

:deep(.token-card) {
  overflow: hidden;
}

/* Ensure scope badges wrap properly and don't overflow */
:deep(.badge),
:deep(.px-2.py-1),
:deep([class*="badge"]) {
  display: inline-block;
  max-width: 100%;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  text-align: left;
  line-height: 1.3;
}

/* Scope container styling */
:deep(.space-y-1 > *),
:deep(.flex.flex-wrap > *) {
  max-width: 100%;
}
</style>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { tokenAPI } from '../services/api'
import TokenCard from '../components/TokenCard.vue'
import RefreshTokenModal from '../components/RefreshTokenModal.vue'
import AuthModal from '../components/AuthModal.vue'
import AnalyzeTokenModal from '../components/AnalyzeTokenModal.vue'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const tokens = ref([])
const loading = ref(false)
const selectedTokens = ref([])
const refreshModalOpen = ref(false)
const selectedRefreshToken = ref(null)
const filterType = ref('all')
const scopeSearch = ref('')
const authModalOpen = ref(false)
const importJwtModalOpen = ref(false)
const importJwtData = ref('')
const jwtPreview = ref(null)
const jwtError = ref('')
const importingJwt = ref(false)
const showAnalyzeModal = ref(false)

// Delete loading states
const deletingExpired = ref(false)
const deletingAll = ref(false)

const filteredTokens = computed(() => {
  let filtered = tokens.value
  
  // Filter by token type
  if (filterType.value !== 'all') {
    filtered = filtered.filter(token => {
      // "Access Tokens" filter includes both regular Access Tokens and Managed Identity tokens
      if (filterType.value === 'access_token') {
        return token.token_type === 'access_token' || token.token_type === 'Managed Identity'
      }
      // Other filters match exactly
      return token.token_type === filterType.value
    })
  }
  
  // Filter by scope, audience or UPN (case-insensitive search)
  if (scopeSearch.value.trim()) {
    const searchLower = scopeSearch.value.toLowerCase().trim()
    filtered = filtered.filter(token => {
      // Search in scope
      if (token.scope && token.scope.toLowerCase().includes(searchLower)) {
        return true
      }
      // Search in audience
      if (token.audience && token.audience.toLowerCase().includes(searchLower)) {
        return true
      }
      // Search in UPN
      if (token.upn && token.upn.toLowerCase().includes(searchLower)) {
        return true
      }
      return false
    })
  }
  
  return filtered
})

const allSelected = computed(() => {
  return filteredTokens.value.length > 0 && 
         filteredTokens.value.every(token => selectedTokens.value.includes(token.id))
})

const hasActiveToken = computed(() => {
  return tokens.value.some(token => token.is_active)
})

const activeTokenId = computed(() => {
  const activeToken = tokens.value.find(token => token.is_active)
  return activeToken ? activeToken.id : null
})

const refreshTokensCount = computed(() => {
  return tokens.value.filter(token => token.has_refresh_token).length
})

const officeMasterCount = computed(() => {
  return tokens.value.filter(token => token.is_office_master).length
})

const expiredTokensCount = computed(() => {
  return tokens.value.filter(token => token.is_expired).length
})

const loadTokens = async () => {
  loading.value = true
  try {
    const response = await tokenAPI.getAll()
    if (response.data.success) {
      tokens.value = response.data.tokens
    }
  } catch (error) {
    console.error('Failed to load tokens:', error)
    alert('Failed to load tokens')
  } finally {
    loading.value = false
  }
}

const toggleSelect = (tokenId) => {
  const index = selectedTokens.value.indexOf(tokenId)
  if (index > -1) {
    selectedTokens.value.splice(index, 1)
  } else {
    selectedTokens.value.push(tokenId)
  }
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    // Deselect all visible tokens
    const visibleIds = filteredTokens.value.map(t => t.id)
    selectedTokens.value = selectedTokens.value.filter(id => !visibleIds.includes(id))
  } else {
    // Select all visible tokens
    const visibleIds = filteredTokens.value.map(t => t.id)
    const newSelections = visibleIds.filter(id => !selectedTokens.value.includes(id))
    selectedTokens.value.push(...newSelections)
  }
}

const deleteSelected = async () => {
  if (!confirm(`Delete ${selectedTokens.value.length} selected token(s)?`)) {
    return
  }
  
  try {
    for (const tokenId of selectedTokens.value) {
      await tokenAPI.delete(tokenId)
    }
    selectedTokens.value = []
    await loadTokens()
    alert('Selected tokens deleted successfully!')
  } catch (error) {
    console.error('Failed to delete tokens:', error)
    alert('Failed to delete some tokens')
  }
}

const deleteExpired = async () => {
  if (!confirm('Delete all expired access tokens?')) {
    return
  }
  
  deletingExpired.value = true
  
  try {
    const response = await tokenAPI.deleteExpired()
    if (response.data.success) {
      await loadTokens()
      alert(`Deleted ${response.data.deleted_count} expired token(s)`)
    } else {
      alert(response.data.error || 'Failed to delete expired tokens')
    }
  } catch (error) {
    console.error('Failed to delete expired tokens:', error)
    alert('Failed to delete expired tokens')
  } finally {
    deletingExpired.value = false
  }
}

const deleteAll = async () => {
  if (!confirm('Delete ALL tokens? This cannot be undone!')) {
    return
  }
  
  if (!confirm('Are you REALLY sure? All tokens will be deleted permanently!')) {
    return
  }
  
  deletingAll.value = true
  const totalTokens = tokens.value.length
  let deletedCount = 0
  
  try {
    // Batch delete in chunks of 10 to avoid overwhelming the server
    const chunkSize = 10
    const tokenChunks = []
    
    for (let i = 0; i < tokens.value.length; i += chunkSize) {
      tokenChunks.push(tokens.value.slice(i, i + chunkSize))
    }
    
    // Process chunks sequentially, but delete within chunk in parallel
    for (const chunk of tokenChunks) {
      await Promise.all(
        chunk.map(token => 
          tokenAPI.delete(token.id).then(() => {
            deletedCount++
            console.log(`Deleted ${deletedCount}/${totalTokens} tokens`)
          }).catch(err => {
            console.error(`Failed to delete token ${token.id}:`, err)
          })
        )
      )
    }
    
    await loadTokens()
    alert(`Successfully deleted ${deletedCount}/${totalTokens} token(s)`)
  } catch (error) {
    console.error('Failed to delete all tokens:', error)
    alert(`Deleted ${deletedCount}/${totalTokens} tokens before error occurred`)
  } finally {
    deletingAll.value = false
  }
}

const activateToken = async (tokenId) => {
  try {
    const response = await tokenAPI.activate(tokenId)
    if (response.data.success) {
      await loadTokens()
      alert('Token activated successfully!')
    }
  } catch (error) {
    console.error('Failed to activate token:', error)
    alert('Failed to activate token')
  }
}

const deleteToken = async (tokenId) => {
  if (!confirm('Are you sure you want to delete this token?')) {
    return
  }
  
  try {
    const response = await tokenAPI.delete(tokenId)
    if (response.data.success) {
      await loadTokens()
      alert('Token deleted successfully!')
    }
  } catch (error) {
    console.error('Failed to delete token:', error)
    alert('Failed to delete token')
  }
}

const clearScopeSearch = () => {
  scopeSearch.value = ''
}

const openRefreshModal = (token) => {
  selectedRefreshToken.value = token
  refreshModalOpen.value = true
}

const closeRefreshModal = () => {
  refreshModalOpen.value = false
  selectedRefreshToken.value = null
}

const handleRefreshSuccess = async () => {
  await loadTokens()
  alert('New access token generated successfully!')
}

const handleAuthSuccess = async (data) => {
  await loadTokens()
  // Don't show alert here, the modal shows success state
}

// Import JWT functions
const openImportJwtModal = () => {
  importJwtModalOpen.value = true
}

const closeImportJwtModal = () => {
  importJwtModalOpen.value = false
  importJwtData.value = ''
  jwtPreview.value = null
  jwtError.value = ''
}

const decodeJwtPreview = () => {
  jwtError.value = ''
  jwtPreview.value = null
  
  const jwt = importJwtData.value.trim()
  if (!jwt) return
  
  const parts = jwt.split('.')
  if (parts.length !== 3) {
    jwtError.value = 'Invalid JWT format: expected 3 parts separated by dots'
    return
  }
  
  try {
    let payload_b64 = parts[1]
    // Add padding if needed
    const padding = 4 - (payload_b64.length % 4)
    if (padding !== 4) {
      payload_b64 += '='.repeat(padding)
    }
    // Replace URL-safe characters
    payload_b64 = payload_b64.replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(payload_b64))
    
    jwtPreview.value = {
      upn: payload.upn || payload.unique_name || payload.preferred_username || 'N/A',
      aud: payload.aud || 'N/A',
      scp: payload.scp || 'N/A',
      exp: payload.exp
    }
  } catch (e) {
    jwtError.value = 'Failed to decode JWT: ' + e.message
  }
}

const formatJwtExpiry = (exp) => {
  if (!exp) return 'N/A'
  const date = new Date(exp * 1000)
  return date.toLocaleString()
}

const importJwt = async () => {
  if (!importJwtData.value.trim()) return
  
  importingJwt.value = true
  try {
    const response = await fetch('http://localhost:5000/api/tokens/import-jwt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jwt: importJwtData.value.trim() })
    })
    const data = await response.json()
    
    if (data.success) {
      closeImportJwtModal()
      await loadTokens()
      alert('JWT imported successfully!')
    } else {
      jwtError.value = data.error || 'Failed to import JWT'
    }
  } catch (e) {
    jwtError.value = 'Failed to import JWT: ' + e.message
  } finally {
    importingJwt.value = false
  }
}

// Watch for JWT input changes to decode preview
watch(importJwtData, () => {
  decodeJwtPreview()
})

const scrollToToken = (tokenId) => {
  // Scroll to the token card
  setTimeout(() => {
    const element = document.querySelector(`[data-token-id="${tokenId}"]`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // Highlight effect
      element.style.transition = 'all 0.3s ease'
      element.style.transform = 'scale(1.02)'
      element.style.boxShadow = '0 0 20px rgba(59, 130, 246, 0.5)'
      setTimeout(() => {
        element.style.transform = 'scale(1)'
        element.style.boxShadow = ''
      }, 600)
    }
  }, 100)
}

onMounted(() => {
  loadTokens()
})
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-lg font-semibold text-sm transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-primary-dark {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-secondary {
  @apply bg-gray-200 text-gray-700 hover:bg-gray-300;
}

.btn-secondary-dark {
  @apply bg-gray-700 text-gray-200 hover:bg-gray-600;
}

.btn-danger {
  @apply bg-red-600 text-white hover:bg-red-700;
}

.btn-danger-outline {
  @apply border-2 border-red-600 text-red-600 hover:bg-red-50;
}

.btn-danger-outline-dark {
  @apply border-2 border-red-500 text-red-400 hover:bg-red-900/30;
}

.btn-warning-outline {
  @apply border-2 border-orange-500 text-orange-600 hover:bg-orange-50;
}

.btn-warning-outline-dark {
  @apply border-2 border-orange-500 text-orange-400 hover:bg-orange-900/30;
}
</style>
