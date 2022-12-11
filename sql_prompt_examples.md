Here are some examples:
Example 1:
===========================================
Input:
how many new cases in the united states in the past week
Output:
SELECT SUM(new_cases) FROM data WHERE iso_code = 'USA' AND date > NOW() - INTERVAL '7 days';

Example 2:
===========================================
Input:
which country had the most new cases in the past week
Output:
SELECT location, SUM(new_cases) FROM data WHERE (date > NOW() - INTERVAL '7 days') and new_cases is not NULL GROUP BY location ORDER BY SUM(new_cases) DESC LIMIT 1;

Example 3:
===========================================
Input:
which continent had the least new deaths in January of 2022
Output:
SELECT continent, sum(new_deaths)
FROM data
WHERE date BETWEEN '2022-01-01' AND '2022-01-31' and new_deaths is not NULL and continent is not NULL
GROUP BY continent
ORDER BY 2 ASC;

Example 4:
===========================================
Input:
which continent had the most new deaths 2 weeks ago
Output:
SELECT continent, SUM(new_deaths) FROM data
WHERE date = (current_date - INTERVAL '2 weeks') AND new_deaths IS NOT NULL AND continent IS NOT NULL
GROUP BY 1 ORDER BY 2 DESC;