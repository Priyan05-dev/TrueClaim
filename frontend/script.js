const form = document.getElementById("uploadForm");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);

    try {
        const res = await fetch("http://127.0.0.1:8000/upload", {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        let color = "black";

        if (data.status === "Approved") {
            color = "green";
        } else if (data.status === "Rejected") {
            color = "red";
        } else if (data.status === "Flagged") {
            color = "orange";
        }

        document.getElementById("result").innerHTML =
            `<span style="color:${color}; font-weight:bold;">
                Status: ${data.status}
            </span><br>
            Explanation: ${data.explanation}`;
    } catch (error) {
        console.error("Error:", error);
    }
});

async function loadClaims() {
    try {
        const res = await fetch("http://127.0.0.1:8000/claims");
        const data = await res.json();

        const list = document.getElementById("claims");
        list.innerHTML = "";

        data.forEach(claim => {
            const li = document.createElement("li");
            li.innerText = `₹${claim[3]} - ${claim[6]} (${claim[7]})`;
            list.appendChild(li);
        });
    } catch (error) {
        console.error(error);
    }
}

async function toggleClaims() {
    const list = document.getElementById("claims");
    const button = document.getElementById("toggleBtn");

    if (!visible) {
        try {
            const res = await fetch("http://127.0.0.1:8000/claims");
            const data = await res.json();

            list.innerHTML = "";

            data.forEach(claim => {
                const li = document.createElement("li");
                li.innerText = `₹${claim[3]} - ${claim[6]} (${claim[7]})`;
                list.appendChild(li);
            });

            button.innerText = "Hide Claims";
            visible = true;

        } catch (error) {
            console.error(error);
        }
    } else {
        list.innerHTML = "";
        button.innerText = "Show Claims";
        visible = false;
    }
}