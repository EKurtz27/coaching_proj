#install.packages("shiny")

library(bslib)
library(shiny)

setwd("C:/Users/Evan/coaching_proj_local")



ui <- fluidPage(
  titlePanel("Team Cohesion Investigation"),
  
  sidebarLayout(
    sidebarPanel(
      selectInput(
        inputId = "display_selection",
        label = "Select desired plot option:",
        choices = c("Histogram of Values", "QQ Plots of Distributions"),
        selected = "Histogram of Values"
      ),
      conditionalPanel(
        condition = "input.display_selection == 'QQ Plots of Distributions'",
        selectInput(
          inputId = "distribution_selection",  # avoid spaces in inputId
          label = "Select distribution:",
          choices = c("Normal", "Exponential"),
          selected = "Normal"
        )
      ),
      selectInput(
        inputId = "year_selection",
        label = "Select a year to access data from:",
        choices = 2020:2025,
        selected = 2020
      )
    ),
    
    mainPanel(
      plotOutput(outputId = "stats_hist")
    )
  )
)

server <- function(input, output, session){
  output$stats_hist <- renderPlot({
    file_path <- sprintf("data/cohesion_stats/%s.csv", input$year_selection)
    stats_df <- read.csv(file_path)
    if (input$display_selection == "Histogram of Values") {
        hist(stats_df$AverageScore, breaks = 30, xlim=c(0, 30))
    }else if (input$display_selection == "QQ Plots of Distributions") {
        avg_scores <- stats_df$AverageScore
        n <- length(avg_scores)
        emperical_cdf <- seq(1, n, 1) / (n + 1)
        actual_quantiles <- sort(avg_scores)
        if (input$distribution_selection == "Normal") {
          ideal_quantiles <- qnorm(emperical_cdf, mean = mean(avg_scores), sd = sd(avg_scores), lower.tail = T)
        }
        else if (input$distribution_selection == "Exponential") {
          ideal_quantiles <- qexp(emperical_cdf, 1 / mean(avg_scores), lower.tail = T)
        }
      plot(ideal_quantiles, actual_quantiles,
      main = "Manual QQ Plot vs Exponential",
      xlab = "Ideal Quantiles",
      ylab = "Actual Quantiles",
      pch = 19)
      abline(0, 1, col = "red")
    }
  })
}

shinyApp(ui = ui, server = server)

