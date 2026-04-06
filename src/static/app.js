document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        const title = document.createElement("h4");
        title.textContent = name;

        const description = document.createElement("p");
        description.textContent = details.description;

        const schedule = document.createElement("p");
        const scheduleLabel = document.createElement("strong");
        scheduleLabel.textContent = "Schedule:";
        schedule.appendChild(scheduleLabel);
        schedule.appendChild(document.createTextNode(` ${details.schedule}`));

        const availability = document.createElement("p");
        const availabilityLabel = document.createElement("strong");
        availabilityLabel.textContent = "Availability:";
        availability.appendChild(availabilityLabel);
        availability.appendChild(document.createTextNode(` ${spotsLeft} spots left`));

        const participantsSection = document.createElement("div");
        participantsSection.className = "participants-section";

        const participantsLabel = document.createElement("strong");
        participantsLabel.textContent = "Participants:";

        const participantsUl = document.createElement("ul");
        participantsUl.className = "participants-list";

        if (details.participants.length > 0) {
          details.participants.forEach((p) => {
            const participantItem = document.createElement("li");

            const participantName = document.createElement("span");
            participantName.textContent = p;

            const deleteButton = document.createElement("button");
            deleteButton.className = "delete-btn";
            deleteButton.dataset.activity = name;
            deleteButton.dataset.email = p;
            deleteButton.title = "Remove participant";
            deleteButton.setAttribute("aria-label", `Remove participant ${p}`);
            deleteButton.setAttribute("aria-label", `Remove participant ${p} from ${name}`);
            deleteButton.textContent = "✕";

            deleteButton.addEventListener("click", async (e) => {
              e.preventDefault();
              const activity = deleteButton.dataset.activity;
              const email = deleteButton.dataset.email;

              try {
                const response = await fetch(
                  `/activities/${encodeURIComponent(activity)}/participants/${encodeURIComponent(email)}`,
                  { method: "DELETE" }
                );

                if (response.ok) {
                  fetchActivities(); // Refresh the list
                } else {
                  const result = await response.json();
                  alert(result.detail || "Failed to remove participant");
                }
              } catch (error) {
                alert("Error removing participant");
                console.error("Error:", error);
              }
            });

            participantItem.appendChild(participantName);
            participantItem.appendChild(deleteButton);
            participantsUl.appendChild(participantItem);
          });
        } else {
          const emptyItem = document.createElement("li");
          emptyItem.style.color = "#999";
          emptyItem.style.fontStyle = "italic";
          emptyItem.textContent = "No participants yet";
          participantsUl.appendChild(emptyItem);
        }

        participantsSection.appendChild(participantsLabel);
        participantsSection.appendChild(participantsUl);

        activityCard.appendChild(title);
        activityCard.appendChild(description);
        activityCard.appendChild(schedule);
        activityCard.appendChild(availability);
        activityCard.appendChild(participantsSection);
        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities(); // Refresh the list to show updated availability
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
