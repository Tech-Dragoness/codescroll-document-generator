/* JS Document */

/******************************

[Table of Contents]

1. Declaration of variables
2. Dropdowns
  a. Collections Dropdown
  b. Archives Dropdown
3. Main Carousel
4. About Us Database Connection
  a. About Us Image
  b. About Us Know More Button
5. Membership & Faculty
6. History Page
7. Timmings Section
  a. General Timmings
  b. Fiction Section Timmings
8. Notice Box
9. Calendar Section
10. Mini Sections
  a. Rules
  b. Facilities
  c. Events
11. Login Section
12. E-Resource Linking
13. Gallery Page
    a. Annual Book Sale
    b. Book Reading
    c. Events and Exhibitions
    d. Quiz Competition
    e. Library History

******************************/

/* 

1. Declaration of variables

*/
let userLoggedIn = localStorage.getItem("userLoggedIn") === "true"; // Retrieve the login state from localStorage

const calendarGrid = document.getElementById("calendar-grid");
const monthYear = document.getElementById("month-year");
const prevMonthBtn = document.getElementById("prev-month");
const nextMonthBtn = document.getElementById("next-month");
const openPopupButton = document.getElementById('open-popup');
const closePopupButton = document.getElementById('close-popup');
const popup = document.getElementById('popup');

let currentDate = new Date();

// Important dates
const importantDates = {};  // This will hold the important dates

/*
2. Dropdowns
*/

/*
a. Collections Dropdown
*/

document.addEventListener("DOMContentLoaded", function () {
    // Fetch collection links using AJAX
    fetch('js/php/fetch_collections.php')
        .then(response => response.json())  // Parse the response as JSON
        .then(data => {
            const collectionLinksContainer = document.getElementById('collection-links');
            if (data.length > 0) {
                // Add each link to the dropdown menu
                data.forEach(link => {
                    const linkElement = document.createElement('div');
                    linkElement.innerHTML = link;
                    collectionLinksContainer.appendChild(linkElement);
                });
            } else {
                collectionLinksContainer.innerHTML = "No documents found.";
            }
        })
        .catch(error => console.error('Error fetching collection links:', error));
});

document.addEventListener("DOMContentLoaded", function () {
    const collectionToggle = document.querySelector(".collection-toggle");
    const collectionList = document.querySelector(".collection-list");
    const menuContainer = document.querySelector(".menu_container");

    collectionToggle.addEventListener("click", function (event) {
        event.preventDefault(); // Prevent default link behavior

        // Toggle the visibility of the submenu
        if (collectionList.style.display === "block") {
            collectionList.style.display = "none";
        } else {
            collectionList.style.display = "block";

            // Fetch collection items if not already loaded
            if (collectionList.innerHTML === "") {
                fetch("js/php/fetch_collections.php")
                    .then(response => response.json())
                    .then(data => {
                        if (data.length > 0) {
                            data.forEach(item => {
                                let listItem = document.createElement("li");
                                listItem.innerHTML = item;
                                collectionList.appendChild(listItem);
                            });
                        } else {
                            collectionList.innerHTML = "<li>No collections available</li>";
                        }
                    })
                    .catch(error => console.error("Error fetching collections:", error));
            }
        }
        // Prevent the main menu from closing
        event.stopPropagation();
    });

    // Close the submenu when the menu is reopened
    menuContainer.addEventListener("transitioned", function () {
        if (!menuContainer.classList.contains("active")) {
            collectionList.style.display = "none"; // Reset submenu on menu close
        }
    });
});

/*
b. Archives Dropdown
*/

document.addEventListener("DOMContentLoaded", function () {
    // Fetch archive links using AJAX
    fetch('js/php/fetch_archives.php')
        .then(response => response.json())  // Parse the response as JSON
        .then(data => {
            const archiveLinksContainer = document.getElementById('archive-links');
            if (data.length > 0) {
                // Add each link to the dropdown menu
                data.forEach(link => {
                    const linkElement = document.createElement('div');
                    linkElement.innerHTML = link;
                    archiveLinksContainer.appendChild(linkElement);
                });
            } else {
                archiveLinksContainer.innerHTML = "No archives found.";
            }
        })
        .catch(error => console.error('Error fetching archive links:', error));
});

document.addEventListener("DOMContentLoaded", function () {
    const archivesToggle = document.querySelector(".archives-toggle");
    const archivesList = document.querySelector(".archives-list");
    const menuContainer = document.querySelector(".menu_container");

    archivesToggle.addEventListener("click", function (event) {
        event.preventDefault(); // Prevent default link behavior

        // Toggle the visibility of the submenu
        if (archivesList.style.display === "block") {
            archivesList.style.display = "none";
        } else {
            archivesList.style.display = "block";

            // Fetch archives items if not already loaded
            if (archivesList.innerHTML === "") {
                fetch("js/php/fetch_archives.php")
                    .then(response => response.json())
                    .then(data => {
                        if (data.length > 0) {
                            data.forEach(item => {
                                let listItem = document.createElement("li");
                                listItem.innerHTML = item;
                                listItem.target = "_blank"; // Open in new tab
                                archivesList.appendChild(listItem);
                            });
                        } else {
                            archivesList.innerHTML = "<li>No archives available</li>";
                        }
                    })
                    .catch(error => console.error("Error fetching archives:", error));
            }
        }
        // Prevent the main menu from closing
        event.stopPropagation();
    });

    // Prevent submenu clicks from closing the menu
    archivesList.addEventListener("click", function (event) {
        event.stopPropagation();
    });

    // Close the submenu when the menu is reopened
    menuContainer.addEventListener("transitionend", function () {
        if (!menuContainer.classList.contains("active")) {
            archivesList.style.display = "none"; // Reset submenu on menu close
        }
    });
});


/*
Login/Logout Button 
*/

// Function to toggle between Login and Logout buttons
function toggleLoginLogout() {
    const loginButtons = document.getElementsByClassName("login-popup");
    const logoutButtons = document.getElementsByClassName("logout-popup");

    if (userLoggedIn) {
        // Show the logout button and hide the login button
        Array.from(loginButtons).forEach(button => button.style.display = "none");
        Array.from(logoutButtons).forEach(button => button.style.display = "inline-block");
    } else {
        // Show the login button and hide the logout button
        Array.from(loginButtons).forEach(button => button.style.display = "inline-block");
        Array.from(logoutButtons).forEach(button => button.style.display = "none");
    }
}

if (!window.location.pathname.includes('eresources.html')) {
    // Call the function to check user status on page load
    toggleLoginLogout();
}

function logOut() {
    userLoggedIn = false;
    localStorage.setItem("userLoggedIn", "false"); // Store the logout state in localStorage
    window.location.href = 'index.html#open-popup'; // Redirect to the homepage or login page
    alert("You have logged out");
    toggleLoginLogout();
}

function eresourcesLogOut() {
    userLoggedIn = false;
    localStorage.setItem("userLoggedIn", "false"); // Store the logout state in localStorage
    window.location.replace("index.html#open-popup"); // Redirect to the homepage or login page
    alert("You have logged out");
}

/*
3. Main Carousel
*/

document.addEventListener('DOMContentLoaded', function () {
    const slideBackgrounds = document.querySelectorAll('.main_carousel_slide_background'); // Select all the slide backgrounds

    fetch('js/php/fetch_carousel_images.php')
        .then(response => response.json())
        .then(images => {
            if (images.length < slideBackgrounds.length) {
                console.warn('Not enough images in the database to fill all slides.');
            }

            slideBackgrounds.forEach((slide, index) => {
                if (images[index]) {
                    // Set the background image for each slide
                    slide.style.backgroundImage = `url(${images[index]})`;
                    slide.style.backgroundSize = 'cover';
                    slide.style.backgroundPosition = 'center';
                    slide.style.height = '100%';
                } else {
                    // Handle missing images (e.g., fallback to a default image)
                    slide.style.backgroundImage = 'url("Main_images/default.jpg")';
                }
            });

            // Initialize OwlCarousel once the images are set
            initmainSlider();
        })
        .catch(error => console.error('Error fetching carousel images:', error));
});


// Move the initmainSlider function outside the DOMContentLoaded event listener
function initmainSlider() {
    if ($('.main_carousel').length) {
        var owl = $('.main_carousel');

        owl.owlCarousel({
            items: 1,
            loop: true,
            smartSpeed: 800,
            autoplay: true,
            nav: false,
            dots: false
        });

        // Add animate.css class(es) to the elements to be animated
        function setAnimation(_elem, _InOut) {
            var animationEndEvent = 'webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend';

            _elem.each(function () {
                var $elem = $(this);
                var $animationType = 'animated ' + $elem.data('animation-' + _InOut);

                $elem.addClass($animationType).one(animationEndEvent, function () {
                    $elem.removeClass($animationType); // Remove animation class after animation ends
                });
            });
        }

        // Fired before current slide change
        owl.on('change.owl.carousel', function (event) {
            var $currentItem = $('.owl-item', owl).eq(event.item.index);
            var $elemsToanim = $currentItem.find("[data-animation-out]");
            setAnimation($elemsToanim, 'out');
        });

        // Fired after current slide has been changed
        owl.on('changed.owl.carousel', function (event) {
            var $currentItem = $('.owl-item', owl).eq(event.item.index);
            var $elemsToanim = $currentItem.find("[data-animation-in]");
            setAnimation($elemsToanim, 'in');
        });

        // Handle Custom Navigation
        if ($('.main_carousel_left').length) {
            var owlPrev = $('.main_carousel_left');
            owlPrev.on('click', function () {
                owl.trigger('prev.owl.carousel');
            });
        }

        if ($('.main_carousel_right').length) {
            var owlNext = $('.main_carousel_right');
            owlNext.on('click', function () {
                owl.trigger('next.owl.carousel');
            });
        }
    }
}



/*
4. About Us Database Connection
*/

/*
a. About Us Image
*/

document.addEventListener("DOMContentLoaded", function () {
    const currentPath = window.location.pathname;

    // Check if it contains "index.html"
    if (currentPath.includes('index.html')) {
        // Fetch the image URL using AJAX
        fetch('js/php/fetch_image.php')
            .then(response => response.json())  // Parse the response as JSON
            .then(data => {
                const imageElement = document.getElementById('library-image');
                imageElement.src = data.image_url;  // Set the image source dynamically
            })
            .catch(error => console.error('Error fetching image URL:', error));
    }
});

/*
b. About Us Know More Button
*/

const currentPath = window.location.pathname;

// Check if the page is "index.html"
if (currentPath.includes('index.html')) {
    // Get button and target section
    const knowMoreButton = document.getElementById("knowMoreButton");
    const detailsSection = document.getElementById("detailsSection");
    const aboutDetails = document.getElementById("aboutDetails");

    // When the 'Know More' button is clicked
    knowMoreButton.addEventListener("click", function () {
        // Toggle visibility
        detailsSection.classList.toggle("hidden");

        // Wait for visibility change, then scroll (only if visible)
        setTimeout(() => {
            if (!detailsSection.classList.contains("hidden")) {
                aboutDetails.scrollIntoView({ behavior: "smooth" });
            }
        }, 100); // Small delay to ensure the class is applied
    });
}

/*
5. Membership & Faculty
*/

// Fetch the faculty data from the PHP script
// Check if it contains "index.html"
if (currentPath.includes('index.html')) {
    fetch('js/php/faculty.php')
        .then(response => response.json())
        .then(data => {
            const currentStaffList = document.getElementById('current-staff-list');
            const exLibrariansList = document.getElementById('ex-librarians-list');
            let libraryAttendants = [];

            data.forEach(faculty => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `<strong>${faculty.staff_type}:</strong> ${faculty.name}, ${faculty.qualifications}`;

                // If Library Attendants are found, group them
                if (faculty.staff_type === 'LIBRARY ATTENDANTS') {
                    libraryAttendants.push(listItem);
                } else if (faculty.position === 'Current Staff') {
                    currentStaffList.appendChild(listItem);
                } else if (faculty.position === 'Ex-Librarians') {
                    exLibrariansList.appendChild(listItem);
                }
            });

            // Now handle the Library Attendants, displaying them once
            if (libraryAttendants.length > 0) {
                const libraryAttendantsHeader = document.createElement('li');
                libraryAttendantsHeader.innerHTML = '<strong>LIBRARY ATTENDANTS:</strong>';
                currentStaffList.appendChild(libraryAttendantsHeader);
                const innerList = document.createElement('ul');
                innerList.classList.add('inner-list');
                libraryAttendants.forEach(attendant => {
                    const innerListItem = document.createElement('li');
                    innerListItem.innerHTML = attendant.innerHTML; // Append name
                    innerList.appendChild(innerListItem);
                });
                currentStaffList.appendChild(innerList);
            }
        })
        .catch(error => console.error('Error fetching faculty data:', error));
}

/*
6. History Page
*/

if (currentPath.includes('history.html')) {
    document.addEventListener("DOMContentLoaded", function () {
        fetch("js/php/fetch_history_images.php")
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error(data.error);
                    return;
                }

                // Get references to elements
                const carouselTrack = document.querySelector(".carousel-track");
                const heroSection = document.querySelector(".hero");
                const historyImage = document.querySelector(".history-image img");

                // Clear existing carousel images
                if (carouselTrack) carouselTrack.innerHTML = "";

                data.forEach(image => {
                    if (image.section_name === "Library_History") {
                        // Populate the carousel
                        let imgElement = document.createElement("img");
                        imgElement.src = image.image_url;
                        imgElement.alt = "Library History";
                        carouselTrack.appendChild(imgElement);
                    } else if (image.section_name === "History_Main") {
                        // Update hero section background
                        if (heroSection) {
                            heroSection.style.backgroundImage = `url('${image.image_url}')`;
                        }
                    } else if (image.section_name === "History_Side") {
                        // Update history image
                        if (historyImage) {
                            historyImage.src = image.image_url;
                        }
                    }
                });
            })
            .catch(error => console.error("Error fetching images:", error));
    });
}

/*
7. Timmings Section
*/

/*
a. General Timmings
*/

// Check if it contains "index.html"
if (currentPath.includes('index.html')) {

    document.addEventListener('DOMContentLoaded', function () {
        const timingsBody = document.getElementById('timings-body');

        fetch('js/php/fetchGeneralTimings.php')
            .then((response) => response.json())
            .then((timings) => {
                if (timings.length === 0) {
                    timingsBody.innerHTML = '<tr><td colspan="3">No timings available at the moment.</td></tr>';
                    return;
                }

                // Populate timings
                timings.forEach((timing) => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
          <td>${timing.week_day}</td>
          <td>${timing.term_hours}</td>
          <td>${timing.vacation_hours}</td>
        `;
                    timingsBody.appendChild(row);
                });
            })
            .catch((error) => {
                console.error('Error fetching timings:', error);
                timingsBody.innerHTML = '<tr><td colspan="3">Error loading timings. Please try again later.</td></tr>';
            });
    });
}

/*
b. Fiction Section Timmings
*/

// Check if it contains "index.html"
if (currentPath.includes('index.html')) {
    fetch('js/php/fetchFictionTimings.php')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('fiction-timings-body');
            data.forEach(timing => {
                const row = document.createElement('tr');
                row.innerHTML = `
                <td>${timing.week_day}</td>
                <td>${timing.term_hours}</td>
            `;
                tableBody.appendChild(row);
            });
        });
}

/*

/*
8. Notices Box
*/

// Check if it contains "index.html"
if (currentPath.includes('index.html')) {
    document.addEventListener('DOMContentLoaded', function () {
        const noticeBox = document.getElementById('notices-box');

        fetch('js/php/fetchNotices.php')
            .then((response) => response.json())
            .then((notices) => {
                if (notices.length === 0) {
                    noticeBox.innerHTML = '<p>No notices available at the moment.</p>';
                    return;
                }

                // Populate notices
                notices.forEach((notice) => {
                    const noticeElement = document.createElement('p');
                    noticeElement.innerHTML = `
          <p>
            <i class="fa-solid fa-caret-right"></i> ${notice.notice_text}
          </p>
        `;
                    noticeBox.appendChild(noticeElement);
                });
            })
            .catch((error) => {
                console.error('Error fetching notices:', error);
                noticeBox.innerHTML = '<p>Error loading notices. Please try again later.</p>';
            });
    });
}


/* 

9. Calendar Section

*/

// Check if it contains "index.html"
if (currentPath.includes('index.html')) {

    // Function to fetch important dates from PHP
    function fetchImportantDates() {
        fetch("js/php/getImportantDates.php")
            .then(response => response.text())  // Get the response as text (HTML content)
            .then(data => {

                // Create a temporary div to parse the HTML response
                const divs = document.createElement("div");
                divs.innerHTML = data; // Insert the HTML content from the PHP response

                // Select all the important divs from the HTML response
                const allImportantDivs = divs.querySelectorAll('.important');

                // Populate the importantDates object with the data from the divs
                allImportantDivs.forEach(function (div) {
                    const dateKey = div.getAttribute('data-date');
                    const description = div.getAttribute('data-tooltip');
                    importantDates[dateKey] = description;
                });

                // Now you can use the importantDates object to generate the calendar
                generateCalendar(currentDate, importantDates);  // Pass importantDates to the calendar generation function
            })
            .catch(error => console.error("Error fetching important dates:", error));
    }

    // Function to generate the calendar
    function generateCalendar(date, importantDates) {
        // Clear the calendar grid
        calendarGrid.innerHTML = "";

        // Get month and year
        const month = date.getMonth();
        const year = date.getFullYear();

        // Update header
        monthYear.textContent = date.toLocaleString("default", { month: "long", year: "numeric" });

        // Get the first and last day of the month
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        // Add empty slots for the days before the 1st of the month
        for (let i = 0; i < firstDay; i++) {
            const emptyDiv = document.createElement("div");
            calendarGrid.appendChild(emptyDiv);
        }

        // Add days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            const dayDiv = document.createElement("div");
            const dateKey = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;

            dayDiv.textContent = day;

            // Mark important dates
            if (importantDates[dateKey]) {
                dayDiv.classList.add("important");
                dayDiv.setAttribute("data-tooltip", importantDates[dateKey]);
            }

            calendarGrid.appendChild(dayDiv);
        }
    }

    // Navigation buttons
    prevMonthBtn.addEventListener("click", () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        generateCalendar(currentDate, importantDates);
    });

    nextMonthBtn.addEventListener("click", () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        generateCalendar(currentDate, importantDates);
    });

    // Initialize calendar and fetch the important dates
    fetchImportantDates();
}

/*
10. Mini Sections
*/

/*
a. Rules
*/

document.addEventListener('DOMContentLoaded', function () {
    // Check if it contains "index.html"
    if (currentPath.includes('index.html')) {
        // Fetch the know more link for the facilities section
        fetch('js/php/fetchKnowMoreLink.php?section=rules')
            .then(response => response.json())
            .then(data => {
                if (data.link) {
                    // Dynamically set the 'Know More' link
                    const knowMoreButton = document.getElementById('know-more-rules');
                    knowMoreButton.href = data.link;
                    knowMoreButton.style.display = 'inline';  // Make the button visible
                }
            })
            .catch(error => console.error('Error fetching Know More link:', error));
    }

});

document.addEventListener('DOMContentLoaded', function () {
    // Check if it contains "index.html"
    if (currentPath.includes('index.html')) {
        const rulesContainer = document.getElementById('rules-container');

        fetch('js/php/fetchRules.php')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (!data || data.length === 0) {
                    rulesContainer.innerHTML = '<p>No rules available at the moment.</p>';
                    return;
                }

                data.forEach(category => {
                    const card = document.createElement('div');
                    card.classList.add('card');
                    card.innerHTML = `
                  <h3>${category.category}</h3>
                  <ul>
                      ${category.rules.map(rule => `<li>${rule}</li>`).join('')}
                  </ul>
              `;
                    rulesContainer.appendChild(card);
                });
            })
            .catch(error => {
                console.error('Error fetching rules:', error);
                rulesContainer.innerHTML = '<p>Error loading rules. Please try again later.</p>';
            });
    }
});

/*
b. Facilities
*/

document.addEventListener('DOMContentLoaded', function () {
    // Check if it contains "index.html"
    if (currentPath.includes('index.html')) {
        // Fetch the know more link for the facilities section
        fetch('js/php/fetchKnowMoreLink.php?section=facilities')
            .then(response => response.json())
            .then(data => {
                if (data.link) {
                    // Dynamically set the 'Know More' link
                    const knowMoreButton = document.getElementById('know-more-facilities');
                    knowMoreButton.href = data.link;
                    knowMoreButton.style.display = 'inline';  // Make the button visible
                }
            })
            .catch(error => console.error('Error fetching Know More link:', error));
    }

});

document.addEventListener('DOMContentLoaded', function () {
    // Check if it contains "index.html"
    if (currentPath.includes('index.html')) {
        const facilitiesGrid = document.querySelector('#facilities-grid');

        fetch('js/php/fetchFacilities.php')
            .then(response => response.text())
            .then(data => {
                facilitiesGrid.innerHTML = data; // Insert the data into the grid
            })
            .catch(error => console.error('Error fetching facilities:', error));
    }
});

/*
c. Events
*/

document.addEventListener('DOMContentLoaded', function () {
    // Check if it contains "index.html"
    if (currentPath.includes('index.html')) {
        // Fetch the know more link for the facilities section
        fetch('js/php/fetchKnowMoreLink.php?section=events')
            .then(response => response.json())
            .then(data => {
                if (data.link) {
                    // Dynamically set the 'Know More' link
                    const knowMoreButton = document.getElementById('know-more-events');
                    knowMoreButton.href = data.link;
                    knowMoreButton.style.display = 'inline';  // Make the button visible
                }
            })
            .catch(error => console.error('Error fetching Know More link:', error));
    }

});

document.addEventListener('DOMContentLoaded', function () {
    // Check if it contains "index.html"
    if (currentPath.includes('index.html')) {
        const eventsGrid = document.querySelector('#events-grid');

        fetch('js/php/fetchEvents.php')
            .then(response => response.text())
            .then(data => {
                eventsGrid.innerHTML = data; // Insert the data into the grid
            })
            .catch(error => console.error('Error fetching events:', error));
    }
});


/* 

11. Login Section

*/

// Wait for the DOM to fully load
document.addEventListener('DOMContentLoaded', () => {
    // Encapsulate popup functionality
    function handlePopup() {
        const openPopupButton = document.getElementById('open-popup');
        const closePopupButton = document.getElementById('close-popup');
        const popup = document.getElementById('popup');
        const popupContent = document.querySelector('.popup-content');

        // Show the popup
        openPopupButton?.addEventListener('click', () => {
            popup.style.display = 'flex'; // Flexbox ensures it's centered
            window.location.hash = 'open-popup'; // Add #open-popup to the URL
        });

        // Hide the popup when the close button is clicked
        closePopupButton?.addEventListener('click', () => {
            popup.style.display = 'none';
            removeHash(); // Remove #open-popup from the URL
        });

        // Hide the popup when clicking outside of the form
        popup?.addEventListener('click', (event) => {
            if (!popupContent.contains(event.target)) {
                popup.style.display = 'none';
                removeHash(); // Remove #open-popup from the URL
            }
        });

        // Utility to remove the hash from the URL
        function removeHash() {
            history.replaceState('', document.title, window.location.pathname + window.location.search);
        }

        // Show the popup if #open-popup is present in the URL on page load
        if (window.location.hash === '#open-popup') {
            popup.style.display = 'flex';
        }
    }


    // Encapsulate form switching functionality
    function handleFormSwitching() {
        const recoveryLink = document.querySelector('.login-form a');
        const loginLink = document.querySelector('.recovery-form a');
        const popup = document.getElementById('popup');

        // Show the recovery form
        recoveryLink?.addEventListener('click', (event) => {
            event.preventDefault(); // Prevent default link behavior
            popup.classList.add('recovery-active'); // Add class to show recovery form
        });

        // Show the login form
        loginLink?.addEventListener('click', (event) => {
            event.preventDefault(); // Prevent default link behavior
            popup.classList.remove('recovery-active'); // Remove class to show login form
        });
    }

    // Encapsulate validation functionality
    function handleValidation() {
        const form = document.getElementById('login-form');
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        const emailError = document.getElementById('email-error');
        const passwordError = document.getElementById('password-error');

        form.addEventListener('submit', (event) => {
            event.preventDefault(); // Prevent form submission

            let valid = true;

            // Clear previous error messages
            emailError.innerHTML = '';
            passwordError.innerHTML = '';

            // Validate email
            const emailValue = emailInput.value.trim();
            if (!/^[\w.]+@sophiacollege\.edu\.in$/.test(emailValue)) {
                emailError.innerHTML = '<span>Please enter registered email id.</span>';
                valid = false;
            }

            // Validate password
            const passwordValue = passwordInput.value;

            // If the form is valid, you can proceed (e.g., submit it or log success)
            if (valid) {

                const formData = new FormData();
                formData.append('email', emailValue);
                formData.append('password', passwordValue); // Assuming you're checking password also

                fetch('js/php/checkCredentials.php', {
                    method: 'POST',
                    body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Clear the form inputs
                            emailInput.value = '';
                            passwordInput.value = '';
                            localStorage.setItem("userLoggedIn", "true"); // Store the login state in localStorage
                            // Redirect on successful login
                            window.location.replace('eresources.html'); // Redirect to your desired page
                        } else {
                            // Show login failure message
                            alert('Login not successful. Please check your email and password.');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('There was an error processing your login request.');
                    });
            }
        });

    }

    function initOtpResendButton(otpsend) {
        const sendOtpButton = document.getElementById(otpsend);
        const phoneNumberInput = document.getElementById('phone-number'); // Phone number input field
        const phoneError = document.getElementById('phone-error');
        let timer = null; // Timer for the countdown

        sendOtpButton.addEventListener('click', (event) => {
            event.preventDefault(); // Prevent the form from submitting and reloading the page
            const phoneNumber = phoneNumberInput.value.trim();
            const regex = /^\d{10}$/; // Matches exactly 10 digits

            if (!regex.test(phoneNumber)) {
                phoneError.innerHTML = '<span>Please enter a valid phone number.</span>';
                return; // Prevent OTP from being sent if the phone number is invalid
            }

            // Check if the phone number exists in the database
            fetch('js/php/checkPhoneNumber.php', {
                method: 'POST',
                body: new URLSearchParams({ phone_number: phoneNumber })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.exists) {
                        sendOtpButton.disabled = true; // Disable the button
                        sendOtpButton.textContent = 'Resend OTP in 5 secs'; // Initial button text

                        phoneError.innerHTML = ''; // Clear the error message
                        // Show an alert that the OTP has been sent
                        setTimeout(() => {
                            alert('OTP sent');
                        }, 10); // Delay by 0 milliseconds to let the browser repaint the UI

                        let countdown = 5; // Countdown duration in seconds

                        // Start the countdown
                        timer = setInterval(() => {
                            countdown--;
                            if (countdown > 0) {
                                sendOtpButton.textContent = `Resend OTP in ${countdown} secs`;
                            } else {
                                clearInterval(timer); // Stop the timer when countdown reaches 0
                                sendOtpButton.disabled = false; // Enable the button
                                sendOtpButton.textContent = 'Resend OTP'; // Change the button text
                            }
                        }, 1000); // Update every second
                    } else {
                        phoneError.innerHTML = '<span>Please enter registered phone number.</span>';
                    }
                })
                .catch(error => {
                    console.error("Error checking phone number:", error);
                });
        });
    }

    if (!window.location.pathname.includes('eresources.html')) {

        // Initialize all functionalities
        handlePopup();
        handleFormSwitching();
        handleValidation();
        initOtpResendButton('otpsend');

    }

});

/* 

12. E-Resource Linking

*/

// Get all elements with the class "e-resources"
const eResourcesLinks = document.getElementsByClassName("e-resources");

// Loop through each element and add the click event listener
for (let i = 0; i < eResourcesLinks.length; i++) {
    eResourcesLinks[i].addEventListener("click", function (event) {
        event.preventDefault(); // Prevent default link behavior
        if (userLoggedIn) {
            // If user is logged in, redirect to the linked resource
            window.location.href = 'eresources.html';
        }
        else {
            document.getElementById("popup").style.display = "flex"; // Show the popup
        }
    });
}

// Handle actions when the page loads
document.addEventListener("DOMContentLoaded", function () {
    const popup = document.getElementById("popup");
    if (popup) {
        // Ensure the popup is hidden by default
        popup.style.display = "none";

        // Check if the URL contains the specific hash
        if (window.location.hash === "#open-popup") {
            popup.style.display = "flex"; // Show the popup only when hash matches
        }
    }
});

/*
13. Gallery Page
*/

/*
a. Annual Book Sale
*/

document.addEventListener("DOMContentLoaded", function () {
    const currentPath = window.location.pathname;

    // Check if it contains "gallery.html"
    if (currentPath.includes('gallery.html')) {
        const galleryContainer = document.getElementById('Annual_Book_Sale');

        fetch('js/php/fetch_annual_book_sale_images.php') // Use the specific PHP file for "Annual Book Sale"
            .then((response) => response.json())
            .then((data) => {
                galleryContainer.innerHTML = "";

                if (data.length > 0) {
                    data.forEach((image) => {
                        const imgElement = document.createElement("div");
                        imgElement.className = "gallery-item";
                        imgElement.innerHTML = `<img src="${image.image_url}" alt="${image.image_name}" />`;
                        galleryContainer.appendChild(imgElement);
                    });
                } else {
                    galleryContainer.innerHTML = `<p class="no-images">No images found for Annual Book Sale.</p>`;
                }
            })
            .catch((error) => {
                console.error('Error fetching images:', error);
                galleryContainer.innerHTML = `<p class="error">An error occurred while loading images.</p>`;
            });
    }
});

/*
b. Book Reading
*/

document.addEventListener("DOMContentLoaded", function () {
    const currentPath = window.location.pathname;

    // Check if it contains "gallery.html"
    if (currentPath.includes('gallery.html')) {
        const galleryContainer = document.getElementById('Book_Reading');

        fetch('js/php/fetch_book_reading_images.php') // Use the specific PHP file for "Book Reading"
            .then((response) => response.json())
            .then((data) => {
                galleryContainer.innerHTML = "";

                if (data.length > 0) {
                    data.forEach((image) => {
                        const imgElement = document.createElement("div");
                        imgElement.className = "gallery-item";
                        imgElement.innerHTML = `<img src="${image.image_url}" alt="${image.image_name}" />`;
                        galleryContainer.appendChild(imgElement);
                    });
                } else {
                    galleryContainer.innerHTML = `<p class="no-images">No images found for Book Reading.</p>`;
                }
            })
            .catch((error) => {
                console.error('Error fetching images:', error);
                galleryContainer.innerHTML = `<p class="error">An error occurred while loading images.</p>`;
            });
    }
});

/*
c. Events and Exhibitions
*/

document.addEventListener("DOMContentLoaded", function () {
    const currentPath = window.location.pathname;

    // Check if it contains "gallery.html"
    if (currentPath.includes('gallery.html')) {
        const galleryContainer = document.getElementById('Events_and_Exhibitions');

        fetch('js/php/fetch_events_and_exhibitions_images.php') // Use the specific PHP file for "Events and Exhibitions"
            .then((response) => response.json())
            .then((data) => {
                galleryContainer.innerHTML = "";

                if (data.length > 0) {
                    data.forEach((image) => {
                        const imgElement = document.createElement("div");
                        imgElement.className = "gallery-item";
                        imgElement.innerHTML = `<img src="${image.image_url}" alt="${image.image_name}" />`;
                        galleryContainer.appendChild(imgElement);
                    });
                } else {
                    galleryContainer.innerHTML = `<p class="no-images">No images found for Events and Exhibitions.</p>`;
                }
            })
            .catch((error) => {
                console.error('Error fetching images:', error);
                galleryContainer.innerHTML = `<p class="error">An error occurred while loading images.</p>`;
            });
    }
});

/*
d.Quiz Competition
*/

document.addEventListener("DOMContentLoaded", function () {
    const currentPath = window.location.pathname;

    // Check if it contains "gallery.html"
    if (currentPath.includes('gallery.html')) {
        const galleryContainer = document.getElementById('Quiz_Competition');

        fetch('js/php/fetch_quiz_competition_images.php') // Use the specific PHP file for "Quiz Competition"
            .then((response) => response.json())
            .then((data) => {
                galleryContainer.innerHTML = "";

                if (data.length > 0) {
                    data.forEach((image) => {
                        const imgElement = document.createElement("div");
                        imgElement.className = "gallery-item";
                        imgElement.innerHTML = `<img src="${image.image_url}" alt="${image.image_name}" />`;
                        galleryContainer.appendChild(imgElement);
                    });
                } else {
                    galleryContainer.innerHTML = `<p class="no-images">No images found for Quiz Competition.</p>`;
                }
            })
            .catch((error) => {
                console.error('Error fetching images:', error);
                galleryContainer.innerHTML = `<p class="error">An error occurred while loading images.</p>`;
            });
    }
});

/*
e. Library History
*/

document.addEventListener("DOMContentLoaded", function () {
    const currentPath = window.location.pathname;

    // Check if it contains "gallery.html"
    if (currentPath.includes('gallery.html')) {
        const galleryContainer = document.getElementById('Library_History');

        fetch('js/php/fetch_library_history_images.php') // Use the specific PHP file for "Library History"
            .then((response) => response.json())
            .then((data) => {
                galleryContainer.innerHTML = "";

                if (data.length > 0) {
                    data.forEach((image) => {
                        const imgElement = document.createElement("div");
                        imgElement.className = "gallery-item";
                        imgElement.innerHTML = `<img src="${image.image_url}" alt="${image.image_name}" />`;
                        galleryContainer.appendChild(imgElement);
                    });
                } else {
                    galleryContainer.innerHTML = `<p class="no-images">No images found for Library History.</p>`;
                }
            })
            .catch((error) => {
                console.error('Error fetching images:', error);
                galleryContainer.innerHTML = `<p class="error">An error occurred while loading images.</p>`;
            });
    }
});
