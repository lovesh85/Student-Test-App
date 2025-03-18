// Initialize Chart.js for student test statistics
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('studentsTestChart').getContext('2d');

    // Fetch real data from API
    fetch('/api/chart-data')
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Average Test Score',
                        data: data.data,
                        fill: false,
                        borderColor: 'rgb(123, 104, 238)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#fff'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#fff'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#fff'
                            }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error fetching chart data:', error));
});

// Profile photo preview
function previewProfilePhoto(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('profilePhotoPreview').src = e.target.result;
            document.getElementById('profilePhotoPreview').style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}