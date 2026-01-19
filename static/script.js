// wait until page ready
document.addEventListener("DOMContentLoaded", () => {
  const filterForm = document.getElementById("filterForm");
  const tableBody  = document.getElementById("commentsTable");
  const addForm    = document.getElementById("addCommentForm");

  // Load all comments initially
  loadComments();

  
  // filter comments (by type)
  
  filterForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const type = filterForm.querySelector("select[name='type']").value
      .trim()
      .toLowerCase();
    loadComments(type);
  });

  
  // load comments (optionally filtered)
  
  async function loadComments(type = "") {
    let url = "/api/comments";
    if (type) {
      url = `/api/comments/type/${type}`;
    }

    try {
      const res  = await fetch(url);
      const data = await res.json();

      tableBody.innerHTML = "";

      if (!res.ok || data.error || !data.length) {
        tableBody.innerHTML = `<tr><td colspan="5" class="muted">No comments found.</td></tr>`;
        showToast("No comments found for selected type.", "error");
        return;
      }

      data.forEach((c) => {
        const typeLower = (c.comment_type || "").toLowerCase();
        const typeLabel =
          typeLower.charAt(0).toUpperCase() + typeLower.slice(1);
        const severity = c.severity
          ? c.severity.charAt(0).toUpperCase() + c.severity.slice(1)
          : "—";

        tableBody.innerHTML += `
          <tr>
            <td>${c.id}</td>
            <td><span class="pill ${typeLower}">${typeLabel}</span></td>
            <td>${c.comment}</td>
            <td>${severity}</td>
            <td>
              <div class="action-buttons">
                <a class="btn-edit" href="/comments/${c.id}/edit">Edit</a>
                <button class="btn-delete" data-id="${c.id}">Delete</button>
              </div>
            </td>
          </tr>`;
      });

      // attach delete handlers
      document.querySelectorAll(".btn-delete").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          const id = e.target.dataset.id;
          if (!confirm(`Delete comment #${id}?`)) return;

          const response = await fetch(`/api/comments/${id}`, {
            method: "DELETE",
          });

          if (response.ok) {
            loadComments();
            showToast("Comment deleted!", "success")
          } else {
            showToast("Failed to delete comment.");
          }
        });
      });

    } catch (err) {
      console.error("Error loading comments:", err);
      tableBody.innerHTML = `<tr><td colspan="5" class="muted">Error loading comments.</td></tr>`;
      showToast("Error loading comments.", "error")
    }
  }

  
  // add new comment (POST)
  
  addForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const type = addForm.querySelector("select[name='type']").value;
    const text = addForm.querySelector("input[name='text']").value;

    if (!type || !text.trim()) {
      showToast("Please fill all fields.", "error");
      return;
    }

    const res = await fetch("/api/comments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        comment_type: type,
        comment: text,
      }),
    });

  if (res.ok) {
    addForm.reset();
    loadComments();
    showToast("Comment added successfully!", "success");
  } else {
    showToast("Failed to add comment.", "error");
  }



  });


  function showToast(message, type = "success") {
    const toast = document.getElementById("toast");

    toast.textContent = message;

    
    toast.classList.remove("hidden");

    
    toast.classList.remove("success", "error");
    
    
    toast.classList.add(type);
    toast.classList.add("show");

    // Hide after 2.5s
    setTimeout(() => {
        toast.classList.remove("show");
        toast.classList.add("hidden");
    }, 2500);
}




});


