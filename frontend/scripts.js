document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById("fileInput");
    const fileLabel = document.getElementById("fileLabel");
    const fileName = document.getElementById("fileName");
    const progressConatiner = document.getElementById("progressConatiner");
    const progressBar = document.getElementById("progressBar");
    const convertBtn = document.getElementById("convertBtn");
    const downloadBtn = document.getElementById("downloadBtn");
    const loader = document.getElementById("loader");
    const status = document.getElementById("status");
    const countdown = document.getElementById("countdown");

    let selectedFile = null;
    let downloadUrl = '';
    let downTimer = null;
    let secondsLeft = 10;

    fileInput.addEventListener('change', function (e) {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            fileName.textContent = selectedFile.name;
            convertBtn.disabled = false;

            const validExtensions = ['xlsx', 'xls'];
            const fileExt = selectedFile.name.split('.').pop().toLowerCase();

            if (!validExtensions.includes(fileExt)) {
                status.textContent = 'Please select a valid Excel file (.xlsx or .xls)';
                status.className = 'status error';
                status.style.display = 'block';
                convertBtn.disabled = true;
            } else {
                status.style.display = 'none';
            }
        } else {
            selectedFile = null;
            fileName.textContent = 'No file selected!';
            convertBtn.disabled = true;
        }
    });

    convertBtn.addEventListener('click', function () {
        if (!selectedFile) return;

        loader.style.display = 'block';
        convertBtn.style.display = 'none';
        fileInput.disabled = true;
        fileLabel.style.opacity = '0.5';
        fileLabel.style.cursor = 'not-allowed';
        progressConatiner.style.display = 'block';

        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            progressBar.style.width = `${progress}%`;
            if (progress >= 100) clearInterval(progressInterval);
        }, 200);

        const formData = new FormData();
        formData.append('file', selectedFile);

        fetch('http://52.73.195.10:8000/upload', {
            method: 'POST',
            body: formData
        })
            .then(response => {
                if (!response.ok) throw new Error('Conversion failed');
                return response.json();
            })
            .then(data => {
                console.log(data.output)
                
                loader.style.display = 'none';
                downloadBtn.style.display = 'inline-block';
                progressConatiner.style.display = 'none';
                fileInput.disabled = true;
                fileLabel.textContent = 'File uploaded';
                downloadUrl = data.output;

            })
            .catch(error => {
                loader.style.display = 'none';
                convertBtn.style.display = 'inline-block';
                progressConatiner.style.display = 'none';
                progressBar.style.width = '0%';
                status.textContent = error.message || 'An error occurred during conversion';
                status.className = 'status error';
                status.style.display = 'block';
                fileInput.disabled = false;
                fileLabel.style.opacity = '1';
                fileLabel.style.cursor = 'pointer';
            });
    });

    downloadBtn.addEventListener('click', function () {
        countdown.style.display = 'block';
        countdown.textContent = `Cache Clear in ${secondsLeft} sec...`;

        downTimer = setInterval(() => {
            secondsLeft--;
            countdown.textContent = `Cache Clear in ${secondsLeft} sec...`;
            if (secondsLeft <= 0) {
                clearInterval(downTimer);
                refreshPage();
            }
        }, 1000);

        // const link = document.createElement('a');
        // link.href = downloadUrl;
        const link = downloadUrl
        link.download = selectedFile.name.replace(/\.[^/.]+$/, "") + ".csv";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        setTimeout(() => {
            fetch('http://52.73.195.10:8000/cleanup', {
                method: 'DELETE',
            })
                .then(() => {
                    console.log('Server cleanup triggered');
                })
                .catch(error => {
                    console.error('Error clearing server:', error);
                });
        }, 1000);
    });

    function refreshPage() {
        window.location.reload();
    }
});
