cd ./youtubedr
go run main.go -info https://www.youtube.com/watch?v=54e6lBE3BoQ
go run main.go -o "test1".mov https://www.youtube.com/watch?v=54e6lBE3BoQ
go run main.go -o "test2".mp4 https://www.youtube.com/watch?v=FHpvI8oGsuQ
go run main.go -o "test3".mp4 https://www.youtube.com/watch?v=n3kPvBCYT3E
go run main.go https://www.youtube.com/watch?v=n3kPvBCYT3E
go run main.go -q medium https://www.youtube.com/watch?v=n3kPvBCYT3E
go run main.go -i 18 https://www.youtube.com/watch?v=n3kPvBCYT3E
go run main.go -i 22 https://www.youtube.com/watch?v=n3kPvBCYT3E  #download should fail
go run main.go -q hd1080 https://www.youtube.com/watch?v=n3kPvBCYT3E  #download 1080p
cd ..
