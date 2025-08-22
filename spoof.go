package main

import (
	"fmt"
	"math/rand"
	"net"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"
)

type ScanResult struct {
	IP     string
	Status string
}

func isPublicIP(ip net.IP) bool {
	if ip == nil || !ip.IsGlobalUnicast() {
		return false
	}
	return true
}

// فقط بررسی کن SSH باز هست یا نه
func checkSSH(ipPort string) bool {
	conn, err := net.DialTimeout("tcp", ipPort, 2*time.Second)
	if err != nil {
		return false
	}
	conn.Close()
	return true
}

func hasPTR(ip string) bool {
	names, err := net.LookupAddr(ip)
	if err != nil || len(names) == 0 {
		return false // PTR نداره
	}
	return true // PTR داره
}

func worker(id int, port string, jobs <-chan struct{}, results chan<- ScanResult) {
	r := rand.New(rand.NewSource(time.Now().UnixNano() + int64(id)))
	for range jobs {
		var ip net.IP
		for {
			ipBytes := make([]byte, 4)
			ipBytes[0] = byte(r.Intn(256))
			ipBytes[1] = byte(r.Intn(256))
			ipBytes[2] = byte(r.Intn(256))
			ipBytes[3] = byte(r.Intn(256))
			ip = net.IPv4(ipBytes[0], ipBytes[1], ipBytes[2], ipBytes[3])
			if isPublicIP(ip) {
				break
			}
		}

		ipPort := ip.String() + ":" + port
		if checkSSH(ipPort) {
			if !hasPTR(ip.String()) {
				results <- ScanResult{IP: ip.String(), Status: "noptr"}
			}
		}
	}
}

func fileSaver(saveQueue <-chan string, wg *sync.WaitGroup) {
	defer wg.Done()
	existingIPs := make(map[string]struct{})

	content, err := os.ReadFile("Good_ip.txt")
	if err == nil {
		lines := strings.Split(string(content), "\n")
		for _, line := range lines {
			if line != "" {
				existingIPs[line] = struct{}{}
			}
		}
	}

	file, err := os.OpenFile("Good_ip.txt", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		fmt.Printf("\nError: Could not open Good_ip.txt for writing: %v\n", err)
		return
	}
	defer file.Close()

	for ip := range saveQueue {
		if _, exists := existingIPs[ip]; !exists {
			_, err := file.WriteString(ip + "\n")
			if err != nil {
				fmt.Printf("\nError writing to file: %v\n", err)
			}
			existingIPs[ip] = struct{}{}
		}
	}
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run file.go <port>")
		return
	}
	port := os.Args[1]

	threadCount := 5000
	jobs := make(chan struct{}, threadCount)
	results := make(chan ScanResult, threadCount)
	done := make(chan struct{})
	var wg sync.WaitGroup

	saveQueue := make(chan string, 1024)
	var saverWg sync.WaitGroup
	saverWg.Add(1)
	go fileSaver(saveQueue, &saverWg)

	for i := 0; i < threadCount; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			worker(id, port, jobs, results)
		}(i)
	}

	go func() {
		for {
			select {
			case <-done:
				return
			case jobs <- struct{}{}:
			}
		}
	}()

	var totalScans, noptrCount int
	var scansInLastSecond int

	statsTicker := time.NewTicker(1 * time.Second)
	defer statsTicker.Stop()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	fmt.Println("Starting scanner... Press Ctrl+C to stop.")

	for {
		select {
		case res := <-results:
			totalScans++
			scansInLastSecond++
			if res.Status == "noptr" {
				saveQueue <- res.IP
				noptrCount++
			}

		case <-statsTicker.C:
			fmt.Printf("\rSpeed: %d/s | Total: %d | NoPTR: %d",
				scansInLastSecond, totalScans, noptrCount)
			scansInLastSecond = 0

		case <-stop:
			fmt.Println("\nGraceful shutdown initiated.")
			close(done)
			close(jobs)
			wg.Wait()
			close(results)

			for res := range results {
				if res.Status == "noptr" {
					saveQueue <- res.IP
				}
			}

			close(saveQueue)
			saverWg.Wait()
			fmt.Printf("\nFinished. Results saved to Good_ip.txt\n")
			return
		}
	}
}