/**
 * Toast UI Editor initialization and form handling
 * Reusable for both create and edit post pages
 */
(function() {
  'use strict';

  function normalizeUrls(markdown) {
    return markdown.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function(match, text, url) {
      if (/^(https?|mailto|ftp|#|\/)/i.test(url)) {
        return match;
      }
      if (url.includes('.') && !url.startsWith('/')) {
        return '[' + text + '](https://' + url + ')';
      }
      return match;
    });
  }

  function fixPopupPosition() {
    if (window.innerWidth > 640) return;
    
    document.querySelectorAll('[class*="toastui-editor-popup"]').forEach(function(popup) {
      // Positioning
      popup.style.position = 'fixed';
      popup.style.left = '0.5rem';
      popup.style.right = '0.5rem';
      popup.style.width = 'calc(100vw - 1rem)';
      popup.style.maxWidth = 'calc(100vw - 1rem)';
      popup.style.transform = 'none';
      popup.style.margin = '0';
      popup.style.zIndex = '10000';
      
      // Ensure background is visible
      popup.style.backgroundColor = '#ffffff';
      popup.style.border = '1px solid #e5e7eb';
      popup.style.borderRadius = '0.5rem';
      popup.style.color = '#111827';
      
      // Fix popup body
      var popupBody = popup.querySelector('[class*="popup-body"]') || popup;
      if (popupBody) {
        popupBody.style.backgroundColor = '#ffffff';
        popupBody.style.color = '#111827';
      }
      
      // Fix inputs and textareas
      popup.querySelectorAll('input, textarea').forEach(function(input) {
        input.style.backgroundColor = '#ffffff';
        input.style.color = '#111827';
        input.style.border = '1px solid #d1d5db';
      });
      
      // Fix labels and text
      popup.querySelectorAll('label, span, p').forEach(function(el) {
        el.style.color = '#111827';
      });
      
      // Center vertically if needed
      var rect = popup.getBoundingClientRect();
      if (rect.top < 0 || rect.bottom > window.innerHeight) {
        popup.style.top = '50%';
        popup.style.transform = 'translateY(-50%)';
      }
    });
  }

  function initToastUIEditor(options) {
    options = options || {};
    var textareaId = options.textareaId || 'id_body';
    var containerId = options.containerId || 'toastui-editor-container';
    var placeholder = options.placeholder || 'Write your post here. Use the toolbar to format your content.';
    var height = options.height || '400px';
    
    var textarea = document.getElementById(textareaId);
    var container = document.getElementById(containerId);
    
    if (!textarea || !container) {
      console.error('Toast UI Editor: Required elements not found');
      return null;
    }
    
    // Hide textarea and remove required attribute
    textarea.style.setProperty('display', 'none', 'important');
    textarea.removeAttribute('required');
    if (!textarea.value) {
      textarea.value = '';
    }
    
    var editor;
    try {
      editor = new toastui.Editor({
        el: container,
        initialEditType: 'wysiwyg',
        height: height,
        initialValue: textarea.value || '',
        placeholder: placeholder,
        toolbarItems: [
          ['heading', 'bold', 'italic', 'strike', 'hr', 'quote'],
          ['ul', 'ol', 'task'],
          ['table', 'link'],
          ['code', 'codeblock']
        ]
      });
      
      // Fix popup positioning on mobile
      setTimeout(function() {
        var observer = new MutationObserver(function() {
          if (document.querySelector('[class*="toastui-editor-popup"]')) {
            fixPopupPosition();
            setTimeout(fixPopupPosition, 50);
          }
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
        window.addEventListener('resize', fixPopupPosition);
      }, 200);
    } catch (e) {
      console.error('Failed to initialize Toast UI Editor:', e);
      textarea.style.display = 'block';
      return null;
    }
    
    // Setup form submission handler
    var form = textarea.closest('form');
    if (form) {
      function syncBody() {
        try {
          if (editor && typeof editor.getMarkdown === 'function') {
            var markdownContent = editor.getMarkdown();
            markdownContent = normalizeUrls(markdownContent);
            textarea.value = markdownContent;
            
            if (!markdownContent.trim()) {
              return { success: false, error: 'Please enter some content for your post.' };
            }
            return { success: true };
          }
        } catch (err) {
          console.error('Error syncing editor content:', err);
          textarea.value = '';
          return { success: false, error: 'Error: Could not save editor content. Please try again.' };
        }
        textarea.value = '';
        return { success: false, error: 'Editor not initialized properly.' };
      }
      
      form.addEventListener('submit', function(e) {
        var result = syncBody();
        if (!result.success) {
          e.preventDefault();
          alert(result.error || 'Please fill in all required fields.');
          return false;
        }
      }, false);
      
      var btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.addEventListener('click', function() {
          syncBody();
        }, false);
      }
    }
    
    return editor;
  }

  // Auto-initialize if DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      if (document.getElementById('toastui-editor-container')) {
        initToastUIEditor();
      }
    });
  } else {
    if (document.getElementById('toastui-editor-container')) {
      initToastUIEditor();
    }
  }

  // Export for manual initialization if needed
  window.initToastUIEditor = initToastUIEditor;
})();
