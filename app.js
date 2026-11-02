/**
 * ============================================================================
 * AURA // NEXUS — Next-Gen E-Commerce Core Logic
 * Modern Vanilla JavaScript with LocalStorage Persistence
 * ============================================================================
 */

// Product Catalog Database
const PRODUCTS = [
  {
    id: 1,
    title: "Orion X-1 Titanium Wireless ANC Headphones",
    price: 349.00,
    originalPrice: 429.00,
    category: "audio",
    badge: "Bestseller",
    badgeType: "bestseller",
    rating: 4.9,
    reviews: 428,
    image: "./assets/hero.jpg",
    specs: ["Titanium Arc", "Neural ANC", "55h Playtime", "Spatial Audio"],
    description: "Engineered with 50mm custom acoustic graphene drivers and active neural noise cancellation that adapts 48,000 times per second. Zero latency Bluetooth 5.4 with lossless LDAC streaming."
  },
  {
    id: 2,
    title: "Apex Chrono Ultra Smartwatch",
    price: 449.00,
    originalPrice: 499.00,
    category: "wearables",
    badge: "Pro Tier",
    badgeType: "pro",
    rating: 4.9,
    reviews: 312,
    image: "./assets/watch.jpg",
    specs: ["Sapphire OLED", "ECG & SpO2", "Titanium Mesh", "14-Day Battery"],
    description: "Edge-to-edge curved OLED glass encased in aerospace-grade titanium. Features real-time biometric telemetry, offline topographical navigation, and 100m water resistance."
  },
  {
    id: 3,
    title: "Aether Clear ANC Wireless Earbuds",
    price: 199.00,
    originalPrice: 249.00,
    category: "audio",
    badge: "Popular",
    badgeType: "popular",
    rating: 4.8,
    reviews: 560,
    image: "./assets/earbuds.jpg",
    specs: ["Transparent Shell", "LED Battery Ring", "40h Total Play", "IPX8 Waterproof"],
    description: "Precision-engineered transparent acoustic chamber housing hybrid dual drivers and low-latency gaming pass-through. Features an illuminated acrylic smart charging case."
  },
  {
    id: 4,
    title: "Valence 75% Custom Mechanical Keyboard",
    price: 229.00,
    originalPrice: 279.00,
    category: "hardware",
    badge: "New Release",
    badgeType: "new",
    rating: 4.9,
    reviews: 184,
    image: "./assets/keyboard.jpg",
    specs: ["Gasket Mount", "Per-Key RGB", "Hot-Swappable", "CNC Aluminum"],
    description: "Full CNC machined anodized aluminum body equipped with silicone sound-dampening gaskets, pre-lubed mechanical linear switches, and frosted polycarbonate keycaps."
  },
  {
    id: 5,
    title: "Nexus Horizon Bio-Sensor Smart Ring",
    price: 289.00,
    originalPrice: 349.00,
    category: "wearables",
    badge: "Trending",
    badgeType: "trending",
    rating: 4.7,
    reviews: 245,
    image: "./assets/smartring.jpg",
    specs: ["Grade 5 Titanium", "Sleep Score", "Waterproof 100M", "7-Day Charge"],
    description: "Featherlight 3-gram titanium smart ring equipped with medical-grade infrared photoplethysmography sensors for uninterrupted sleep phase tracking and metabolic readiness."
  },
  {
    id: 6,
    title: "Aether 4K Stealth Autonomous Drone",
    price: 799.00,
    originalPrice: 899.00,
    category: "drones",
    badge: "Limited Drop",
    badgeType: "limited",
    rating: 4.9,
    reviews: 119,
    image: "./assets/drone.jpg",
    specs: ["3-Axis Gimbal", "4K 60fps HDR", "LiDAR Sensors", "42-Min Flight"],
    description: "Ultra-compact folding carbon-fiber quadcopter featuring omnidirectional optical-flow obstacle avoidance, 12km HD video transmission, and AI cinematic tracking."
  },
  {
    id: 7,
    title: "Aura Vision One AR Smart Glasses",
    price: 599.00,
    originalPrice: 699.00,
    category: "optics",
    badge: "Futuristic",
    badgeType: "pro",
    rating: 4.8,
    reviews: 88,
    image: "./assets/glasses.jpg",
    specs: ["Micro-OLED Waveguide", "Spatial Audio", "48g Weight", "Voice AI Assistant"],
    description: "Titanium smart eyewear featuring transparent dual waveguide heads-up displays, real-time live navigation turn prompts, and whisper-quiet beamforming audio transducers."
  }
];

// Currency Configurations
const CURRENCIES = {
  USD: { symbol: "$", rate: 1.0 },
  EUR: { symbol: "€", rate: 0.92 },
  GBP: { symbol: "£", rate: 0.79 }
};

// Store State
let currentCurrency = localStorage.getItem("aura_currency") || "USD";
let activeCategory = "all";
let activeFilterTag = "all";
let currentSort = "featured";
let searchQuery = "";

let cart = JSON.parse(localStorage.getItem("aura_cart") || "[]");
let wishlist = JSON.parse(localStorage.getItem("aura_wishlist") || "[]");
let appliedDiscount = JSON.parse(localStorage.getItem("aura_discount") || "null");

// Coupon codes
const VALID_COUPONS = {
  CYBER20: { code: "CYBER20", rate: 0.20, label: "20% OFF" },
  AURA15: { code: "AURA15", rate: 0.15, label: "15% OFF" },
  WELCOME10: { code: "WELCOME10", rate: 0.10, label: "10% OFF" }
};

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initCurrency();
  setupEventListeners();
  renderProducts();
  updateCartUI();
  updateWishlistUI();
});

// ============================================================================
// Theme Management (Dark / Light)
// ============================================================================
function initTheme() {
  const savedTheme = localStorage.getItem("aura_theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeIcon(savedTheme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const newTheme = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("aura_theme", newTheme);
  updateThemeIcon(newTheme);
  showToast("Theme Updated", `Switched to ${newTheme} mode.`, "info");
}

function updateThemeIcon(theme) {
  const iconSpan = document.getElementById("themeIcon");
  if (iconSpan) {
    iconSpan.textContent = theme === "dark" ? "☀️" : "🌙";
  }
}

// ============================================================================
// Currency Conversion
// ============================================================================
function initCurrency() {
  const select = document.getElementById("currencySelector");
  if (select) {
    select.value = currentCurrency;
    select.addEventListener("change", (e) => {
      currentCurrency = e.target.value;
      localStorage.setItem("aura_currency", currentCurrency);
      renderProducts();
      updateCartUI();
      showToast("Currency Changed", `Displaying prices in ${currentCurrency}`, "info");
    });
  }
}

function formatPrice(amountInUSD) {
  const curr = CURRENCIES[currentCurrency] || CURRENCIES.USD;
  const converted = amountInUSD * curr.rate;
  return `${curr.symbol}${converted.toFixed(2)}`;
}

// ============================================================================
// Event Listeners
// ============================================================================
function setupEventListeners() {
  // Theme button
  const themeBtn = document.getElementById("themeToggleBtn");
  if (themeBtn) themeBtn.addEventListener("click", toggleTheme);

  // Cart toggles
  const cartBtn = document.getElementById("cartToggleBtn");
  if (cartBtn) cartBtn.addEventListener("click", () => toggleCartDrawer(true));

  // Wishlist toggle
  const wishlistBtn = document.getElementById("wishlistToggleBtn");
  if (wishlistBtn) wishlistBtn.addEventListener("click", openWishlistModal);

  // Search input
  const searchInput = document.getElementById("searchInput");
  const searchClear = document.getElementById("searchClearBtn");

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value.trim().toLowerCase();
      if (searchClear) {
        searchClear.classList.toggle("active", searchQuery.length > 0);
      }
      renderProducts();
    });
  }

  if (searchClear) {
    searchClear.addEventListener("click", () => {
      searchInput.value = "";
      searchQuery = "";
      searchClear.classList.remove("active");
      renderProducts();
      searchInput.focus();
    });
  }

  // Category Pills in subnav
  const categoryPills = document.querySelectorAll(".category-pill");
  categoryPills.forEach(pill => {
    pill.addEventListener("click", () => {
      categoryPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeCategory = pill.getAttribute("data-category");
      renderProducts();
    });
  });

  // Filter Buttons in catalog bar
  const filterBtns = document.querySelectorAll(".filter-btn");
  filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeFilterTag = btn.getAttribute("data-filter");
      renderProducts();
    });
  });

  // Sort selector
  const sortSelector = document.getElementById("sortSelector");
  if (sortSelector) {
    sortSelector.addEventListener("change", (e) => {
      currentSort = e.target.value;
      renderProducts();
    });
  }

  // Close modals on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeAllModals();
    }
  });
}

// ============================================================================
// Product Filtering & Rendering
// ============================================================================
function filterByCategory(category) {
  activeCategory = category;
  const pills = document.querySelectorAll(".category-pill");
  pills.forEach(p => {
    p.classList.toggle("active", p.getAttribute("data-category") === category);
  });
  renderProducts();

  const catalogElem = document.getElementById("catalogSection");
  if (catalogElem) {
    catalogElem.scrollIntoView({ behavior: "smooth" });
  }
}

function getFilteredProducts() {
  return PRODUCTS.filter(p => {
    // 1. Category match
    if (activeCategory !== "all" && p.category !== activeCategory) {
      return false;
    }

    // 2. Tag filter
    if (activeFilterTag === "bestseller" && p.badgeType !== "bestseller") return false;
    if (activeFilterTag === "new" && p.badgeType !== "new") return false;
    if (activeFilterTag === "under300" && p.price >= 300) return false;

    // 3. Search query
    if (searchQuery) {
      const matchTitle = p.title.toLowerCase().includes(searchQuery);
      const matchDesc = p.description.toLowerCase().includes(searchQuery);
      const matchCat = p.category.toLowerCase().includes(searchQuery);
      const matchSpecs = p.specs.some(s => s.toLowerCase().includes(searchQuery));
      if (!matchTitle && !matchDesc && !matchCat && !matchSpecs) return false;
    }

    return true;
  }).sort((a, b) => {
    if (currentSort === "price-asc") return a.price - b.price;
    if (currentSort === "price-desc") return b.price - a.price;
    if (currentSort === "rating") return b.rating - a.rating;
    return a.id - b.id; // Default featured
  });
}

function renderProducts() {
  const grid = document.getElementById("productsGrid");
  const counter = document.getElementById("catalogCounter");
  if (!grid) return;

  const filtered = getFilteredProducts();

  if (counter) {
    counter.textContent = `Showing ${filtered.length} product${filtered.length === 1 ? '' : 's'}`;
  }

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div class="empty-catalog">
        <span style="font-size: 3rem; display: block; margin-bottom: 0.5rem;">🔍</span>
        <h3>No matching hardware found</h3>
        <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Try adjusting your search criteria or resetting filters.</p>
        <button class="btn-primary" onclick="resetAllFilters()">Reset All Filters</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = filtered.map(product => {
    const isSaved = wishlist.includes(product.id);
    const badgeClass = product.badgeType === "bestseller" ? "bestseller" : 
                       product.badgeType === "limited" ? "limited" : "";

    return `
      <article class="product-card" id="product-${product.id}">
        <div class="card-image-wrap" onclick="openQuickView(${product.id})">
          <span class="card-badge ${badgeClass}">${product.badge}</span>
          <button 
            class="card-wishlist-btn ${isSaved ? 'active' : ''}" 
            title="${isSaved ? 'Remove from wishlist' : 'Add to wishlist'}"
            onclick="event.stopPropagation(); toggleWishlist(${product.id})"
            aria-label="Save to wishlist"
          >
            ${isSaved ? '❤️' : '🤍'}
          </button>
          <img src="${product.image}" alt="${product.title}" class="card-image" loading="lazy">
          <button class="card-quickview-btn" onclick="event.stopPropagation(); openQuickView(${product.id})">
            🔍 Quick Spec View
          </button>
        </div>

        <div class="card-body">
          <span class="card-category">${product.category}</span>
          <h3 class="card-title" onclick="openQuickView(${product.id})">${product.title}</h3>
          
          <div class="card-specs-tags">
            ${product.specs.slice(0, 3).map(s => `<span class="spec-tag">${s}</span>`).join('')}
          </div>

          <div class="card-rating">
            <span>★★★★★</span>
            <span style="color: var(--text-main); font-weight: 700;">${product.rating.toFixed(1)}</span>
            <span class="card-rating-count">(${product.reviews})</span>
          </div>

          <div class="card-footer">
            <div class="card-price-group">
              <span class="card-price-current">${formatPrice(product.price)}</span>
              ${product.originalPrice ? `<span class="card-price-original">${formatPrice(product.originalPrice)}</span>` : ''}
            </div>
            <button class="card-add-btn" id="addBtn-${product.id}" onclick="quickAddToCart(${product.id})">
              <span>+ Add to Cart</span>
            </button>
          </div>
        </div>
      </article>
    `;
  }).join('');
}

function resetAllFilters() {
  activeCategory = "all";
  activeFilterTag = "all";
  currentSort = "featured";
  searchQuery = "";

  const searchInput = document.getElementById("searchInput");
  if (searchInput) searchInput.value = "";

  document.querySelectorAll(".category-pill").forEach(p => {
    p.classList.toggle("active", p.getAttribute("data-category") === "all");
  });

  document.querySelectorAll(".filter-btn").forEach(b => {
    b.classList.toggle("active", b.getAttribute("data-filter") === "all");
  });

  const sortSelect = document.getElementById("sortSelector");
  if (sortSelect) sortSelect.value = "featured";

  renderProducts();
}

// ============================================================================
// Shopping Cart Functionality
// ============================================================================
function quickAddToCart(productId) {
  addToCart(productId, 1);

  // Button feedback animation
  const btn = document.getElementById(`addBtn-${productId}`);
  if (btn) {
    btn.classList.add("added");
    btn.innerHTML = `<span>✓ Added</span>`;
    setTimeout(() => {
      btn.classList.remove("added");
      btn.innerHTML = `<span>+ Add to Cart</span>`;
    }, 1500);
  }
}

function addToCart(productId, quantity = 1) {
  const product = PRODUCTS.find(p => p.id === productId);
  if (!product) return;

  const existingIndex = cart.findIndex(item => item.id === productId);

  if (existingIndex > -1) {
    cart[existingIndex].quantity += quantity;
  } else {
    cart.push({
      id: product.id,
      title: product.title,
      price: product.price,
      image: product.image,
      quantity: quantity
    });
  }

  saveCart();
  updateCartUI();
  toggleCartDrawer(true);
  showToast("Added to Cart", `${product.title} added to your bag.`, "success");
}

function updateCartQuantity(productId, delta) {
  const index = cart.findIndex(item => item.id === productId);
  if (index === -1) return;

  cart[index].quantity += delta;
  if (cart[index].quantity <= 0) {
    cart.splice(index, 1);
  }

  saveCart();
  updateCartUI();
}

function removeFromCart(productId) {
  const item = cart.find(i => i.id === productId);
  cart = cart.filter(i => i.id !== productId);
  saveCart();
  updateCartUI();
  if (item) {
    showToast("Item Removed", `${item.title} removed from bag.`, "info");
  }
}

function saveCart() {
  localStorage.setItem("aura_cart", JSON.stringify(cart));
}

function updateCartUI() {
  const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
  const subtotalUSD = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  // Badges and counts
  const badge = document.getElementById("cartBadge");
  const drawerCount = document.getElementById("drawerCartCount");
  const headerTotal = document.getElementById("headerCartTotal");

  if (badge) badge.textContent = totalItems;
  if (drawerCount) drawerCount.textContent = totalItems;
  if (headerTotal) headerTotal.textContent = formatPrice(subtotalUSD);

  // Free shipping progress calculation ($150 threshold)
  const freeShippingThreshold = 150;
  const progressPercent = Math.min(100, Math.round((subtotalUSD / freeShippingThreshold) * 100));
  const progressBar = document.getElementById("shippingProgressBar");
  const shippingText = document.getElementById("shippingText");
  const shippingPercent = document.getElementById("shippingPercent");

  if (progressBar && shippingText && shippingPercent) {
    progressBar.style.width = `${progressPercent}%`;
    shippingPercent.textContent = `${progressPercent}%`;

    if (subtotalUSD >= freeShippingThreshold) {
      shippingText.innerHTML = `🎉 <strong>Congratulations!</strong> You qualify for <strong>FREE Worldwide Express Dispatch</strong>`;
    } else {
      const remaining = freeShippingThreshold - subtotalUSD;
      shippingText.innerHTML = `Add <strong>${formatPrice(remaining)}</strong> more for <strong>Free Worldwide Shipping</strong>`;
    }
  }

  // Items List
  const itemsContainer = document.getElementById("cartItemsList");
  if (!itemsContainer) return;

  if (cart.length === 0) {
    itemsContainer.innerHTML = `
      <div class="cart-empty-message">
        <span>🛍️</span>
        <h4 style="font-size: 1.15rem; margin-bottom: 0.5rem; color: var(--text-main);">Your bag is empty</h4>
        <p style="font-size: 0.85rem; margin-bottom: 1.5rem;">Explore our cutting-edge audio and wearable hardware collection.</p>
        <button class="btn-primary" onclick="toggleCartDrawer(false)" style="margin: 0 auto;">Start Exploring</button>
      </div>
    `;
  } else {
    itemsContainer.innerHTML = cart.map(item => `
      <div class="cart-item">
        <div class="cart-item-thumb">
          <img src="${item.image}" alt="${item.title}">
        </div>
        <div class="cart-item-details">
          <h4 class="cart-item-title">${item.title}</h4>
          <span class="cart-item-price">${formatPrice(item.price)}</span>
          <div class="cart-item-stepper">
            <button class="stepper-btn" onclick="updateCartQuantity(${item.id}, -1)" aria-label="Decrease quantity">−</button>
            <span class="stepper-value">${item.quantity}</span>
            <button class="stepper-btn" onclick="updateCartQuantity(${item.id}, 1)" aria-label="Increase quantity">+</button>
          </div>
        </div>
        <button class="cart-item-remove" onclick="removeFromCart(${item.id})" title="Remove item" aria-label="Remove item">
          🗑️
        </button>
      </div>
    `).join('');
  }

  // Calculate Discounts
  let discountUSD = 0;
  if (appliedDiscount) {
    discountUSD = subtotalUSD * appliedDiscount.rate;
  }

  const finalTotalUSD = Math.max(0, subtotalUSD - discountUSD);

  const subtotalElem = document.getElementById("cartSubtotal");
  const discountLine = document.getElementById("discountLine");
  const discountElem = document.getElementById("cartDiscount");
  const discountName = document.getElementById("discountName");
  const totalElem = document.getElementById("cartFinalTotal");

  if (subtotalElem) subtotalElem.textContent = formatPrice(subtotalUSD);
  
  if (discountLine && discountElem && discountName) {
    if (appliedDiscount && discountUSD > 0) {
      discountLine.style.display = "flex";
      discountName.textContent = appliedDiscount.label;
      discountElem.textContent = `-${formatPrice(discountUSD)}`;
    } else {
      discountLine.style.display = "none";
    }
  }

  if (totalElem) totalElem.textContent = formatPrice(finalTotalUSD);
}

function applyDiscountCoupon() {
  const input = document.getElementById("couponInput");
  if (!input) return;

  const rawCode = input.value.trim().toUpperCase();
  if (!rawCode) {
    showToast("Invalid Coupon", "Please enter a valid discount code.", "error");
    return;
  }

  if (VALID_COUPONS[rawCode]) {
    appliedDiscount = VALID_COUPONS[rawCode];
    localStorage.setItem("aura_discount", JSON.stringify(appliedDiscount));
    updateCartUI();
    showToast("Coupon Applied!", `${appliedDiscount.label} discount has been activated.`, "success");
    input.value = "";
  } else {
    showToast("Unknown Code", "Code not found. Try CYBER20 for 20% off.", "error");
  }
}

function resetCart() {
  cart = [];
  appliedDiscount = null;
  saveCart();
  localStorage.removeItem("aura_discount");
  updateCartUI();
}

function toggleCartDrawer(open = true) {
  const drawer = document.getElementById("cartDrawer");
  const overlay = document.getElementById("backdropOverlay");
  if (!drawer || !overlay) return;

  if (open) {
    drawer.classList.add("open");
    overlay.classList.add("active");
    document.body.style.overflow = "hidden";
  } else {
    drawer.classList.remove("open");
    overlay.classList.remove("active");
    document.body.style.overflow = "";
  }
}

// ============================================================================
// Wishlist Management
// ============================================================================
function toggleWishlist(productId) {
  const product = PRODUCTS.find(p => p.id === productId);
  if (!product) return;

  const index = wishlist.indexOf(productId);
  if (index > -1) {
    wishlist.splice(index, 1);
    showToast("Removed from Wishlist", `${product.title} removed.`, "info");
  } else {
    wishlist.push(productId);
    showToast("Saved to Wishlist", `${product.title} saved to favorites.`, "pink");
  }

  localStorage.setItem("aura_wishlist", JSON.stringify(wishlist));
  updateWishlistUI();
  renderProducts();
}

function updateWishlistUI() {
  const badge = document.getElementById("wishlistBadge");
  if (badge) {
    badge.textContent = wishlist.length;
    badge.style.display = wishlist.length > 0 ? "flex" : "none";
  }
}

function openWishlistModal() {
  const modal = document.getElementById("wishlistModal");
  const body = document.getElementById("wishlistItemsBody");
  const countSpan = document.getElementById("wishlistModalCount");
  const overlay = document.getElementById("backdropOverlay");

  if (!modal || !body || !overlay) return;

  const savedProducts = PRODUCTS.filter(p => wishlist.includes(p.id));
  if (countSpan) countSpan.textContent = savedProducts.length;

  if (savedProducts.length === 0) {
    body.innerHTML = `
      <div style="text-align: center; padding: 2rem 1rem;">
        <span style="font-size: 2.5rem; display: block; margin-bottom: 0.5rem;">❤️</span>
        <h4>Your Wishlist is Empty</h4>
        <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Click the heart icon on any product to save it for later.</p>
        <button class="btn-primary" onclick="closeWishlistModal()">Continue Browsing</button>
      </div>
    `;
  } else {
    body.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        ${savedProducts.map(p => `
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-glass);">
            <div style="display: flex; align-items: center; gap: 1rem;">
              <img src="${p.image}" alt="${p.title}" style="width: 60px; height: 60px; object-fit: cover; border-radius: var(--radius-sm);">
              <div>
                <h4 style="font-size: 0.95rem; font-weight: 700;">${p.title}</h4>
                <span style="color: var(--accent-cyan); font-weight: 700; font-size: 0.9rem;">${formatPrice(p.price)}</span>
              </div>
            </div>
            <div style="display: flex; gap: 0.5rem;">
              <button class="btn-primary" onclick="quickAddToCart(${p.id}); closeWishlistModal();" style="padding: 0.45rem 0.9rem; font-size: 0.82rem;">
                + Add to Cart
              </button>
              <button class="action-btn" onclick="toggleWishlist(${p.id}); openWishlistModal();" title="Remove" style="width: 34px; height: 34px;">
                ✕
              </button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  modal.classList.add("open");
  overlay.classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeWishlistModal() {
  const modal = document.getElementById("wishlistModal");
  const overlay = document.getElementById("backdropOverlay");
  if (modal) modal.classList.remove("open");
  if (overlay) overlay.classList.remove("active");
  document.body.style.overflow = "";
}

// ============================================================================
// Quick View Modal
// ============================================================================
function openQuickView(productId) {
  const product = PRODUCTS.find(p => p.id === productId);
  if (!product) return;

  const modal = document.getElementById("quickViewModal");
  const content = document.getElementById("quickViewContent");
  const overlay = document.getElementById("backdropOverlay");

  if (!modal || !content || !overlay) return;

  const isSaved = wishlist.includes(product.id);

  content.innerHTML = `
    <div class="quickview-image-wrap">
      <img src="${product.image}" alt="${product.title}">
    </div>

    <div class="quickview-info">
      <span class="card-category">${product.category} • ${product.badge}</span>
      <h2 style="font-family: var(--font-display); font-size: 1.6rem; font-weight: 800; line-height: 1.2;">${product.title}</h2>

      <div class="card-rating">
        <span>★★★★★</span>
        <span style="color: var(--text-main); font-weight: 700;">${product.rating.toFixed(1)}</span>
        <span class="card-rating-count">(${product.reviews} customer reviews)</span>
      </div>

      <div style="display: flex; align-items: baseline; gap: 0.75rem; margin: 0.5rem 0;">
        <span style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 900; color: var(--accent-cyan);">
          ${formatPrice(product.price)}
        </span>
        ${product.originalPrice ? `<span style="font-size: 1.1rem; color: var(--text-muted); text-decoration: line-through;">${formatPrice(product.originalPrice)}</span>` : ''}
        <span style="font-size: 0.75rem; font-weight: 800; color: var(--accent-emerald); background: rgba(16, 185, 129, 0.15); padding: 0.2rem 0.5rem; border-radius: 4px;">
          IN STOCK — DISPATCHES TODAY
        </span>
      </div>

      <p style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.6;">
        ${product.description}
      </p>

      <div style="margin: 0.5rem 0;">
        <h4 style="font-size: 0.85rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 0.5rem;">HARDWARE ARCHITECTURE</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
          ${product.specs.map(spec => `
            <div style="background: var(--bg-card); border: 1px solid var(--border-glass); padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.82rem; display: flex; align-items: center; gap: 0.4rem;">
              <span style="color: var(--accent-cyan);">⚡</span>
              <span>${spec}</span>
            </div>
          `).join('')}
        </div>
      </div>

      <div style="display: flex; gap: 0.75rem; margin-top: 1rem;">
        <button class="btn-primary" onclick="addToCart(${product.id}, 1); closeQuickView();" style="flex: 1;">
          <span>⚡ Add to Bag (${formatPrice(product.price)})</span>
        </button>
        <button class="action-btn" onclick="toggleWishlist(${product.id}); openQuickView(${product.id});" title="Wishlist" style="width: 48px; height: 48px;">
          ${isSaved ? '❤️' : '🤍'}
        </button>
      </div>
    </div>
  `;

  modal.classList.add("open");
  overlay.classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeQuickView() {
  const modal = document.getElementById("quickViewModal");
  const overlay = document.getElementById("backdropOverlay");
  if (modal) modal.classList.remove("open");
  if (overlay) overlay.classList.remove("active");
  document.body.style.overflow = "";
}

// ============================================================================
// Checkout Flow & Order Processing
// ============================================================================
function openCheckoutModal() {
  if (cart.length === 0) {
    showToast("Empty Bag", "Add items to your cart before proceeding to checkout.", "error");
    return;
  }

  toggleCartDrawer(false);

  const modal = document.getElementById("checkoutModal");
  const overlay = document.getElementById("backdropOverlay");
  const formStep = document.getElementById("checkoutFormStep");
  const successStep = document.getElementById("checkoutSuccessStep");
  const totalAmountElem = document.getElementById("checkoutTotalAmount");

  if (!modal || !overlay) return;

  // Calculate final total
  const subtotalUSD = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  let discountUSD = 0;
  if (appliedDiscount) discountUSD = subtotalUSD * appliedDiscount.rate;
  const finalTotal = Math.max(0, subtotalUSD - discountUSD);

  if (totalAmountElem) totalAmountElem.textContent = formatPrice(finalTotal);

  if (formStep) formStep.style.display = "block";
  if (successStep) successStep.style.display = "none";

  modal.classList.add("open");
  overlay.classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeCheckoutModal() {
  const modal = document.getElementById("checkoutModal");
  const overlay = document.getElementById("backdropOverlay");
  if (modal) modal.classList.remove("open");
  if (overlay) overlay.classList.remove("active");
  document.body.style.overflow = "";
}

function selectPaymentMethod(method, element) {
  document.querySelectorAll(".payment-opt").forEach(btn => btn.classList.remove("active"));
  element.classList.add("active");

  const cardDetails = document.getElementById("cardPaymentDetails");
  if (cardDetails) {
    cardDetails.style.display = method === "card" ? "block" : "none";
  }
}

function processOrderCheckout() {
  const firstName = document.getElementById("checkoutFirstName")?.value.trim();
  const email = document.getElementById("checkoutEmail")?.value.trim();
  const address = document.getElementById("checkoutAddress")?.value.trim();

  if (!firstName || !email || !address) {
    showToast("Required Fields Missing", "Please provide your name, shipping address, and email.", "error");
    return;
  }

  const confirmBtn = document.getElementById("confirmOrderBtn");
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = `<span>⏳ Authorizing Quantum Payment...</span>`;
  }

  // Simulate payment gateway delay
  setTimeout(() => {
    const formStep = document.getElementById("checkoutFormStep");
    const successStep = document.getElementById("checkoutSuccessStep");
    const orderNumberSpan = document.getElementById("confirmedOrderNumber");
    const receiptEmailSpan = document.getElementById("receiptEmail");

    const randomOrderNum = "AUR-" + Math.floor(10000 + Math.random() * 90000);

    if (orderNumberSpan) orderNumberSpan.textContent = `ORDER #${randomOrderNum}`;
    if (receiptEmailSpan) receiptEmailSpan.textContent = email;

    if (formStep) formStep.style.display = "none";
    if (successStep) successStep.style.display = "flex";

    // Launch celebratory confetti fireworks
    launchConfetti();
    showToast("Payment Successful!", `Order #${randomOrderNum} placed successfully.`, "success");

    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = `<span>Complete Order & Authorize Payment</span>`;
    }
  }, 1200);
}

// ============================================================================
// Confetti Animation Canvas
// ============================================================================
function launchConfetti() {
  const canvas = document.getElementById("confettiCanvas");
  if (!canvas) return;

  canvas.style.display = "block";
  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const particles = [];
  const colors = ["#00f0ff", "#8b5cf6", "#ec4899", "#10b981", "#fbbf24", "#ffffff"];

  for (let i = 0; i < 90; i++) {
    particles.push({
      x: canvas.width / 2,
      y: canvas.height / 2,
      vx: (Math.random() - 0.5) * 14,
      vy: (Math.random() - 0.8) * 16,
      size: Math.random() * 8 + 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      rotation: Math.random() * 360,
      vRot: (Math.random() - 0.5) * 8,
      alpha: 1
    });
  }

  let animationFrame;
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let alive = false;

    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.35; // gravity
      p.rotation += p.vRot;
      p.alpha -= 0.012;

      if (p.alpha > 0) {
        alive = true;
        ctx.save();
        ctx.globalAlpha = p.alpha;
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
        ctx.restore();
      }
    });

    if (alive) {
      animationFrame = requestAnimationFrame(animate);
    } else {
      cancelAnimationFrame(animationFrame);
      canvas.style.display = "none";
    }
  }

  animate();
}

// ============================================================================
// VIP Newsletter Form Handler
// ============================================================================
function handleNewsletter(event) {
  event.preventDefault();
  const input = document.getElementById("newsletterEmail");
  if (!input) return;

  const email = input.value.trim();
  if (email) {
    showToast("VIP Access Granted! ⚡", "Use code CYBER20 for 20% off your order.", "success");
    input.value = "";
  }
}

// ============================================================================
// Close All Modals Helper
// ============================================================================
function closeAllModals() {
  toggleCartDrawer(false);
  closeQuickView();
  closeWishlistModal();
  closeCheckoutModal();
}

// ============================================================================
// Toast Notification Engine
// ============================================================================
function showToast(title, message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type === 'success' ? 'toast-success' : type === 'pink' ? 'toast-pink' : ''}`;

  const icon = type === "success" ? "✓" : type === "pink" ? "❤️" : type === "error" ? "⚠️" : "⚡";

  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(40px)";
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}
