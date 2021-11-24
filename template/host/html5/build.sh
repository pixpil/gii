EXPORTED_FUNCTIONS="['_malloc','_RefreshContext','_Cleanup','_onKeyDown','_onKeyUp','_onMouseButton','_onMouseDrag','_onMouseMove','_onPaint','_onReshape','_onTimer','_AKULoadFuncFromString','_AKULoadFuncFromFile','_AKUCallFunc','_OpenWindowFunc','_AKUSetWorkingDirectory','_AKUGetSimStep','_AKUEnqueueKeyboardShiftEvent','_AKUEnqueueKeyboardControlEvent','_AKUEnqueueKeyboardAltEvent','_RestoreFile','_AKUInitializeUntz','_MoaiOpenWindowFunc','_MoaiSaveFunc']"
emcc -O2 -s ASM_JS=0  -s TOTAL_MEMORY=248554432 -s FULL_ES2=1 \
-s WARN_ON_UNDEFINED_SYMBOLS=1 \
--js-library moaicallbacks.js \
--js-library library_webuntz.js \
--pre-js libmoai-pre.js \
--post-js libmoai-post.js \
-s EXPORTED_FUNCTIONS="${EXPORTED_FUNCTIONS}" \
-s INVOKE_RUN=0 \
-L/Volumes/prj/moai/lib/html5 \
libmoaijs.so \
-lfreetype -ltess2 -ltinyxml -ltlsf -luntz -lwebp -lzlib -lpng -lcontrib -lbox2d -ljansson \
-lliblua-static \
-lmoai-core -lzlcore -lzlvfs -lmoai-sim -lmoai-box2d -lmoai-util -lmoai-crypto \
-o moaijs.js\
