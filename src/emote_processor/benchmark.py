import os
import time
import numpy as np
import matplotlib.pyplot as plt

from src.emote_processor.get_emote import get_emotions

backends = ['opencv', 'ssd', 'mtcnn', 'retinaface']
emotions = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

def run_benchmark():
    benchmark_dir = 'benchmark_results'
    os.makedirs(benchmark_dir, exist_ok=True)

    image_list = []
    for emotion in emotions:
        emotion_dir = os.path.join('test_images', emotion)
        if not os.path.exists(emotion_dir):
            continue
        for img_name in os.listdir(emotion_dir):
            img_path = os.path.join(emotion_dir, img_name)
            if os.path.isfile(img_path):
                image_list.append((img_path, emotion))

    # Store accuracy data for heatmap
    accuracy_list = []

    # Benchmark each backend
    for backend in backends:
        total_correct = 0
        total_emotes = 0

        correct_counts = {e: 0 for e in emotions}
        emote_counts = {e: 0 for e in emotions}

        processing_times = []
        
        for idx, (img_path, true_emotion) in enumerate(image_list):
            start_time = time.time()
            try:
                result = get_emotions(img_path, backend) or {}
            except Exception as e:
                print(f"Error processing {img_path} with {backend}: {e}")
                continue
            elapsed = time.time() - start_time
            processing_times.append(elapsed)
            
            pred_emotion = result.get('dominant_emotion', '').lower()
            if true_emotion in emotions:
                emote_counts[true_emotion] += 1
                total_emotes += 1
                if pred_emotion == true_emotion:
                    correct_counts[true_emotion] += 1
                    total_correct += 1

        # Calculate performance metrics
        init_time = processing_times[0] if processing_times else 0
        total_time = sum(processing_times)
        total_excl_init = total_time - init_time
        avg_time = total_excl_init / (len(processing_times) - 1) if len(processing_times) > 1 else 0

        # Calculate accuracy percentages
        accuracy = {}
        for emotion in emotions:
            total = emote_counts[emotion]
            accuracy[emotion] = correct_counts[emotion] / total if total > 0 else 0.0
        
        accuracy_list.append((backend, accuracy))

        # Save benchmark results
        with open(os.path.join(benchmark_dir, f'{backend}.txt'), 'w') as f:
            f.write(f"Metrics for {backend}:\n")
            f.write(f"Initialization Time: {init_time:.4f}s\n")
            f.write(f"Total Processing Time: {total_time:.4f}s\n")
            f.write(f"Time Excluding Initialization: {total_excl_init:.4f}s\n")
            f.write(f"Average Time per Image: {avg_time:.4f}s\n\n")
            f.write("Accuracy Breakdown:\n")
            f.write(f"Average: {total_correct / total_emotes if total_emotes > 0 else 0.0}\n")
            for emotion, acc in accuracy.items():
                f.write(f"{emotion}: {acc:.4f}\n")

    # Generate heatmap visualization
    plt.figure(figsize=(12, 8))

    # Prepare data matrix
    heatmap_data = np.zeros((len(backends), len(emotions)))
    for i, (backend, acc_dict) in enumerate(accuracy_list):
        for j, emotion in enumerate(emotions):
            heatmap_data[i, j] = acc_dict[emotion]

    # Create plot
    plt.imshow(heatmap_data, cmap='inferno', aspect='auto', vmin=0, vmax=1)
    plt.xticks(np.arange(len(emotions)), emotions, rotation=45, ha='right')
    plt.yticks(np.arange(len(backends)), backends)
    plt.title("Emotion Recognition Accuracy Heatmap")
    plt.colorbar(label='Accuracy Score')

    # Add text annotations
    for i in range(len(backends)):
        for j in range(len(emotions)):
            plt.text(j, i, f"{heatmap_data[i, j]:.2f}",
                    ha="center", va="center",
                    color="white" if heatmap_data[i, j] < 0.5 else "black")

    plt.tight_layout()
    plt.savefig(os.path.join(benchmark_dir, 'accuracy_heatmap.png'))
    plt.close()

    print("Benchmarking completed. Results saved in benchmark_results/")
