import simpy
import numpy as np
import pandas as pd
import streamlit as st

# Função para gerar a tabela de voos com assentos premium randomizados
def generate_schedule():
    times = ["0:40", "1:20", "1:45", "1:50", "4:05", "9:15", "10:05", "10:35", "11:50", "13:50",
             "14:15", "14:15", "14:40", "15:30", "16:00", "17:05", "17:10", "17:40", "18:00", "18:00"]
    schedule = []
    for time in times:
        seats_premium = np.random.randint(20, 100)  # Randomiza entre 20 e 100 assentos premium
        schedule.append(("CIA AEREA NOS ARES", time, seats_premium))
    return schedule

# Converte o horário para minutos desde a meia-noite
def time_to_minutes(time_str):
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes

# Simulação
def generate_premium_passengers(env, schedule, passenger_arrivals):
    for entry in schedule:
        cia, time_str, premium_seats = entry
        departure_time = time_to_minutes(time_str)
        for _ in range(premium_seats):
            arrival_time = departure_time - np.random.uniform(30, 120)
            if arrival_time < 0:
                arrival_time += 24 * 60  # Ajusta para ser positivo dentro do intervalo de 24 horas
            passenger_arrivals.append((env.now + arrival_time, env.now + arrival_time))
            yield env.timeout(arrival_time - env.now)
            env.process(passenger(env, arrival_time))

def passenger(env, arrival_time):
    if attendants is not None:
        with attendants.request() as request:
            yield request | env.timeout(0)
            if request.triggered:
                start_service = env.now
                service_time = max(0, np.random.normal(AVG_SERVICE_TIME, 1))
                yield env.timeout(service_time)
                end_service = env.now
                attended_passengers.append((arrival_time, start_service, end_service))
            else:
                denied_passengers.append(arrival_time)
    else:
        denied_passengers.append(arrival_time)

def run_simulation(schedule, num_attendants):
    global attendants, attended_passengers, denied_passengers
    attended_passengers = []
    denied_passengers = []
    env = simpy.Environment()
    attendants = simpy.Resource(env, capacity=num_attendants) if num_attendants > 0 else None
    passenger_arrivals = []
    env.process(generate_premium_passengers(env, schedule, passenger_arrivals))
    env.run(until=max(time_to_minutes(entry[1]) for entry in schedule) + 60)
    
    attended_df = pd.DataFrame(attended_passengers, columns=['Tempo de Chegada', 'Início do Atendimento', 'Final do Atendimento'])
    denied_df = pd.DataFrame(denied_passengers, columns=['Tempo de Chegada'])
    utilization = (len(attended_df) * AVG_SERVICE_TIME) / (len(schedule) * 24 * num_attendants) if num_attendants > 0 else 0
    
    return attended_df, denied_df, utilization

# Parâmetros iniciais
AVG_SERVICE_TIME = 3  # horas

# Streamlit interface
st.title("Simulação de Atendimento de Passageiros Premium no Lounge")
num_attendants = st.slider("Número de atendentes", 0, 10, 3)
avg_service_time = st.slider("Tempo médio de serviço (horas)", 1, 5, 3)

if st.button("Rodar Simulação"):
    schedule = generate_schedule()  # Gerar a tabela de voos com assentos premium randomizados
    attended_df, denied_df, utilization = run_simulation(schedule, num_attendants)
    
    st.write("### Resultados da Simulação")
    st.write(f"Passageiros atendidos: {len(attended_df)}")
    st.write(f"Passageiros negados: {len(denied_df)}")
    st.write(f"Taxa de utilização dos atendentes: {utilization:.2%}")
    
    st.write("### Detalhes dos Passageiros Atendidos")
    st.dataframe(attended_df)
    
    st.write("### Detalhes dos Passageiros Negados")
    st.dataframe(denied_df)
