document.addEventListener('DOMContentLoaded', () => {
    // === DOM Elements ===
    // Sections
    const searchSection = document.getElementById('searchSection');
    const confirmSection = document.getElementById('confirmSection');
    const noMatchSection = document.getElementById('noMatchSection');
    const resultSection = document.getElementById('resultSection');

    // Inputs
    const brandSelect = document.getElementById('brandSelect');
    const modelInput = document.getElementById('modelInput');
    const errorMessage = document.getElementById('errorMessage');

    // Buttons
    const searchBtn = document.getElementById('searchBtn');
    const btnYes = document.getElementById('btnYes');
    const btnNo = document.getElementById('btnNo');
    const btnSearchAgain = document.getElementById('btnSearchAgain');
    const btnStop = document.getElementById('btnStop');
    const btnNewSearch = document.getElementById('btnNewSearch');

    // Display Elements
    const confirmImg = document.getElementById('confirmImg');

    // Mock Data for "Submariner" or default search
    const mockWatchData = {
        brand: "Rolex 勞力士",
        name: "Submariner Date",
        model: "126610LN",
        officialPrice: "NT$ 341,000",
        marketPrice: "NT$ 420,000 ~ 480,000",
        size: "41",
        lugToLug: "47.6",
        material: "Oystersteel 蠔式鋼",
        strap: "Oystersteel 蠔式鋼 (三排鏈節)",
        power: "70",
        functions: "時、分、秒、日期顯示、停秒功能",
        images: {
            confirm: "./assets/watch_front.png",
            front: "./assets/watch_front.png",
            side: "./assets/watch_side.png",
            back: "./assets/watch_back.png"
        }
    };

    // === Helper Functions ===
    function showSection(sectionToShow) {
        // Hide all sections first
        const allSections = [searchSection, confirmSection, noMatchSection, resultSection];
        
        allSections.forEach(sec => {
            sec.classList.remove('active');
            sec.classList.add('hidden'); // Immediately hide for stability in tests
        });

        // Show the target section
        sectionToShow.classList.remove('hidden');
        // Force a reflow
        void sectionToShow.offsetWidth;
        sectionToShow.classList.add('active');
        
        console.log(`Switching to section: ${sectionToShow.id}`);
    }

    // === Event Listeners ===
    
    // 1. Search Button Click
    searchBtn.addEventListener('click', async () => {
        const query = modelInput.value.trim();
        const brand = brandSelect.value;
        if (!query) {
            errorMessage.classList.remove('hidden');
            modelInput.focus();
            return;
        }
        errorMessage.classList.add('hidden');
        
        // 更新按鈕狀態為載入中
        const originalBtnText = searchBtn.textContent;
        searchBtn.textContent = '正在為您全球檢索中...';
        searchBtn.disabled = true;

        try {
            // 呼叫我們的本地 Python AI 伺服器
            const response = await fetch(`/api/search?brand=${encodeURIComponent(brand)}&query=${encodeURIComponent(query)}`);
            const result = await response.json();
            
            if (result.success || result.data) {
                // 將爬取/AI回覆的資料覆蓋到我們的 mockWatchData 以供確認頁與詳細結果頁使用
                const fetchedData = result.data;
                mockWatchData.brand = fetchedData.brand || brand || "-";
                mockWatchData.name = fetchedData.name || query;
                mockWatchData.model = fetchedData.model || "-";
                mockWatchData.officialPrice = fetchedData.officialPrice || "-";
                mockWatchData.marketPrice = fetchedData.marketPrice || "-";
                mockWatchData.size = fetchedData.size || "-";
                mockWatchData.lugToLug = fetchedData.lugToLug || "-";
                mockWatchData.material = fetchedData.material || "-";
                mockWatchData.strap = fetchedData.strap || "-";
                mockWatchData.power = fetchedData.power || "-";
                mockWatchData.functions = fetchedData.functions || "-";
                
                // 動態替換圖片 (即便為 "-" 也要更新，以便前端隱藏區塊)
                if (fetchedData.frontImageUrl) {
                    mockWatchData.images.front = fetchedData.frontImageUrl;
                    mockWatchData.images.confirm = fetchedData.frontImageUrl;
                }
                if (fetchedData.sideImageUrl) {
                    mockWatchData.images.side = fetchedData.sideImageUrl;
                }
                if (fetchedData.backImageUrl) {
                    mockWatchData.images.back = fetchedData.backImageUrl;
                }
                
                if(!result.success) {
                    console.log("提示：API 查詢受限，已使用智慧降級資料庫回覆。");
                }
            } else {
                alert('搜尋失敗：' + (result.error || '未知錯誤'));
                searchBtn.textContent = originalBtnText;
                searchBtn.disabled = false;
                return;
            }
        } catch (err) {
            console.error('API Error:', err);
            alert('後端伺服器未啟動或連線失敗。');
        } finally {
            searchBtn.textContent = originalBtnText;
            searchBtn.disabled = false;
        }
        
        // 繼續原本的 UI 流程：顯示確認圖片區塊
        const confirmTextPlaceholder = document.getElementById('confirmTextPlaceholder');
        
        const showPlaceholder = () => {
            confirmImg.classList.add('hidden');
            confirmTextPlaceholder.classList.remove('hidden');
        };

        const showImage = () => {
            confirmImg.classList.remove('hidden');
            confirmTextPlaceholder.classList.add('hidden');
        };

        if (mockWatchData.images.confirm && mockWatchData.images.confirm !== "-") {
            confirmImg.src = mockWatchData.images.confirm;
            showImage();
            // Remove shimmer after image load
            confirmImg.onload = () => {
                confirmImg.classList.remove('shimmer');
            };
            // If image fails to load, show placeholder
            confirmImg.onerror = showPlaceholder;
        } else {
            showPlaceholder();
        }
        showSection(confirmSection);
    });

    // 2. Confirm: YES
    btnYes.addEventListener('click', () => {
        // Populate the data table
        document.getElementById('specBrand').textContent = mockWatchData.brand;
        document.getElementById('specName').textContent = mockWatchData.name;
        document.getElementById('specModel').textContent = mockWatchData.model;
        document.getElementById('specOfficialPrice').textContent = mockWatchData.officialPrice;
        document.getElementById('specMarketPrice').textContent = mockWatchData.marketPrice;
        document.getElementById('specSize').textContent = mockWatchData.size;
        document.getElementById('specLug').textContent = mockWatchData.lugToLug;
        document.getElementById('specMaterial').textContent = mockWatchData.material;
        document.getElementById('specStrap').textContent = mockWatchData.strap;
        document.getElementById('specPower').textContent = mockWatchData.power;
        document.getElementById('specFunctions').textContent = mockWatchData.functions;

        // Populate images
        // Populate images
        const galleryFront = document.getElementById('galleryFront');
        const gallerySide = document.getElementById('gallerySide');
        const galleryBack = document.getElementById('galleryBack');

        // Front is mandatory, but still check if it's "-" to show placeholder
        const frontTextPlaceholder = document.getElementById('frontTextPlaceholder');
        if (mockWatchData.images.front && mockWatchData.images.front !== "-") {
            galleryFront.src = mockWatchData.images.front;
            galleryFront.classList.remove('hidden');
            frontTextPlaceholder.classList.add('hidden');
            galleryFront.onerror = () => {
                galleryFront.classList.add('hidden');
                frontTextPlaceholder.classList.remove('hidden');
            };
        } else {
            galleryFront.classList.add('hidden');
            frontTextPlaceholder.classList.remove('hidden');
        }

        // Side and Back are conditional
        if (mockWatchData.images.side && mockWatchData.images.side !== "-") {
            gallerySide.src = mockWatchData.images.side;
            gallerySide.parentElement.classList.remove('hidden');
        } else {
            console.log("Hiding side image");
            gallerySide.parentElement.classList.add('hidden');
        }

        if (mockWatchData.images.back && mockWatchData.images.back !== "-") {
            galleryBack.src = mockWatchData.images.back;
            galleryBack.parentElement.classList.remove('hidden');
        } else {
            console.log("Hiding back image");
            galleryBack.parentElement.classList.add('hidden');
        }

        showSection(resultSection);
    });

    // 3. Confirm: NO
    btnNo.addEventListener('click', () => {
        showSection(noMatchSection);
    });

    // 4. Search Again
    btnSearchAgain.addEventListener('click', () => {
        modelInput.value = '';
        brandSelect.value = '';
        showSection(searchSection);
        setTimeout(() => modelInput.focus(), 500);
    });

    // 5. Stop Search
    btnStop.addEventListener('click', () => {
        // Reset and go back to origin
        modelInput.value = '';
        brandSelect.value = '';
        showSection(searchSection);
    });

    // 6. New Search from Result
    btnNewSearch.addEventListener('click', () => {
        modelInput.value = '';
        brandSelect.value = '';
        showSection(searchSection);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    // Support "Enter" key on input
    modelInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchBtn.click();
        }
    });
});
