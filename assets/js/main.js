/* ==========================================================================
   湖南科技大学 建筑与设计学院 宣传报道部 —— 站点交互脚本
   原生 JS，无任何依赖。所有功能在缺失对应 DOM 时自动跳过。
   ========================================================================== */
(function () {
  "use strict";

  var prefersReduced = window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
    : false;

  /* ---------- 1. 顶栏滚动态 ---------- */
  function initHeader() {
    var header = document.getElementById("siteHeader");
    var toTop = document.getElementById("toTop");

    function onScroll() {
      var y = window.scrollY || window.pageYOffset;
      if (header) header.classList.toggle("is-scrolled", y > 8);
      if (toTop) toTop.classList.toggle("is-visible", y > 520);
    }

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    if (toTop) {
      toTop.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: prefersReduced ? "auto" : "smooth" });
      });
    }
  }

  /* ---------- 2. 移动端导航 ---------- */
  function initNav() {
    var btn = document.getElementById("menuBtn");
    var nav = document.getElementById("primaryNav");
    if (!btn || !nav) return;

    function setOpen(open) {
      document.body.classList.toggle("nav-open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.setAttribute("aria-label", open ? "关闭导航菜单" : "打开导航菜单");
    }

    btn.addEventListener("click", function () {
      setOpen(!document.body.classList.contains("nav-open"));
    });

    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setOpen(false);
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 980) setOpen(false);
    });
  }

  /* ---------- 3. 主题切换（浅色/深色） ---------- */
  function initTheme() {
    var KEY = "hnust-xb-theme";
    var root = document.documentElement;
    var btn = document.getElementById("themeToggle");

    function apply(theme) {
      root.setAttribute("data-theme", theme);
      if (btn) {
        var isDark = theme === "dark";
        btn.setAttribute("aria-label", isDark ? "切换到浅色主题" : "切换到深色主题");
        btn.setAttribute("title", isDark ? "切换到浅色主题" : "切换到深色主题");
      }
      var meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute("content", theme === "dark" ? "#0b1220" : "#0a3b6f");
    }

    var stored = null;
    try {
      stored = window.localStorage.getItem(KEY);
    } catch (err) {
      stored = null;
    }

    if (!stored) {
      stored =
        window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";
    }
    apply(stored);

    if (btn) {
      btn.addEventListener("click", function () {
        var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
        apply(next);
        try {
          window.localStorage.setItem(KEY, next);
        } catch (err) {
          /* 隐私模式下忽略 */
        }
      });
    }
  }

  /* ---------- 4. 滚动入场 ---------- */
  function initReveal() {
    var items = document.querySelectorAll(".reveal");
    if (!items.length) return;

    if (prefersReduced || !("IntersectionObserver" in window)) {
      Array.prototype.forEach.call(items, function (el) {
        el.classList.add("is-visible");
      });
      return;
    }

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          var delay = parseInt(el.getAttribute("data-delay") || "0", 10);
          window.setTimeout(function () {
            el.classList.add("is-visible");
          }, delay);
          io.unobserve(el);
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );

    Array.prototype.forEach.call(items, function (el) {
      io.observe(el);
    });
  }

  /* ---------- 5. 数字滚动 ---------- */
  function initCounters() {
    var nums = document.querySelectorAll("[data-count]");
    if (!nums.length || prefersReduced) return;

    function run(el) {
      var target = parseFloat(el.getAttribute("data-count"));
      if (isNaN(target)) return;
      var unit = el.querySelector(".unit");
      var suffix = unit ? unit.outerHTML : "";
      var decimals = (el.getAttribute("data-count").split(".")[1] || "").length;
      var duration = 1200;
      var start = null;

      function frame(ts) {
        if (start === null) start = ts;
        var p = Math.min((ts - start) / duration, 1);
        var eased = 1 - Math.pow(1 - p, 3);
        var value = (target * eased).toFixed(decimals);
        el.innerHTML = value + suffix;
        if (p < 1) window.requestAnimationFrame(frame);
      }

      window.requestAnimationFrame(frame);
    }

    if (!("IntersectionObserver" in window)) {
      Array.prototype.forEach.call(nums, run);
      return;
    }

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          run(entry.target);
          io.unobserve(entry.target);
        });
      },
      { threshold: 0.4 }
    );

    Array.prototype.forEach.call(nums, function (el) {
      io.observe(el);
    });
  }

  /* ---------- 6. 作品分类筛选 ---------- */
  function initFilter() {
    var bar = document.querySelector(".filter-bar");
    if (!bar) return;
    var buttons = bar.querySelectorAll(".filter-btn");
    var cards = document.querySelectorAll("[data-category]");
    if (!buttons.length || !cards.length) return;

    bar.addEventListener("click", function (e) {
      var btn = e.target.closest(".filter-btn");
      if (!btn) return;

      Array.prototype.forEach.call(buttons, function (b) {
        b.classList.toggle("is-active", b === btn);
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });

      var filter = btn.getAttribute("data-filter");
      Array.prototype.forEach.call(cards, function (card) {
        var match = filter === "all" || card.getAttribute("data-category") === filter;
        card.classList.toggle("is-hidden", !match);
      });
    });
  }

  /* ---------- 7. 当前页导航高亮（兜底） ---------- */
  function initActiveNav() {
    var path = window.location.pathname.split("/").pop() || "index.html";
    var links = document.querySelectorAll(".nav-link");
    Array.prototype.forEach.call(links, function (link) {
      var href = (link.getAttribute("href") || "").split("/").pop();
      if (href === path) link.classList.add("is-active");
    });
  }

  /* ---------- 8. 年份 ---------- */
  function initYear() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-year]"), function (el) {
      el.textContent = String(new Date().getFullYear());
    });
  }

  /* ---------- 启动 ---------- */
  function boot() {
    initHeader();
    initNav();
    initTheme();
    initReveal();
    initCounters();
    initFilter();
    initActiveNav();
    initYear();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
